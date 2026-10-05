import logging
import ssl
import sys
from typing import Any

import httpx
import truststore
from mcp.server.fastmcp import FastMCP
from reliability import retry_async


logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("s7085-meals")
mcp = FastMCP("meals")
API_BASE = "https://www.themealdb.com/api/json/v1/1"
REQUEST_TIMEOUT_SECONDS = 3.0


class MealDBClient:
    def __init__(self, base_url: str = API_BASE, timeout: float = REQUEST_TIMEOUT_SECONDS):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.verify_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    async def _get_once(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout, verify=self.verify_context) as client:
            response = await client.get(f"{self.base_url}/{endpoint}", params=params)
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("response JSON must be an object")
            return payload

    async def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        def transient_error(error: Exception) -> bool:
            if isinstance(error, httpx.HTTPStatusError):
                return error.response.status_code >= 500
            return isinstance(error, (httpx.TransportError, TimeoutError))

        try:
            return await retry_async(
                lambda: self._get_once(endpoint, params),
                timeout_seconds=self.timeout,
                max_attempts=3,
                should_retry=transient_error,
            )
        except (httpx.HTTPError, TimeoutError, ValueError) as exc:
            logger.error("MealDB request failed for %s: %s", endpoint, exc)
            raise RuntimeError(f"TheMealDB request failed: {type(exc).__name__}") from exc

    @staticmethod
    def _empty_result() -> dict[str, Any]:
        return {"meals": [], "message": "No matches"}

    @staticmethod
    def _meal_card(meal: dict[str, Any], include_area: bool) -> dict[str, Any]:
        card = {
            "id": str(meal.get("idMeal", "")),
            "name": meal.get("strMeal", ""),
            "thumb": meal.get("strMealThumb", ""),
        }
        if include_area:
            card["area"] = meal.get("strArea") or ""
            card["category"] = meal.get("strCategory") or ""
        return card

    @staticmethod
    def _meal_details(meal: dict[str, Any]) -> dict[str, Any]:
        ingredients = []
        for index in range(1, 21):
            name = (meal.get(f"strIngredient{index}") or "").strip()
            measure = (meal.get(f"strMeasure{index}") or "").strip()
            if name:
                ingredients.append({"name": name, "measure": measure})
        return {
            "id": str(meal.get("idMeal", "")),
            "name": meal.get("strMeal", ""),
            "category": meal.get("strCategory") or "",
            "area": meal.get("strArea") or "",
            "instructions": meal.get("strInstructions") or "",
            "image": meal.get("strMealThumb") or "",
            "source": meal.get("strSource") or "",
            "youtube": meal.get("strYoutube") or "",
            "ingredients": ingredients,
        }

    async def search_meals_by_name(self, query: str, limit: int = 5) -> dict[str, Any]:
        if not query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= limit <= 25:
            raise ValueError("limit must be between 1 and 25")
        meals = (await self._get("search.php", {"s": query.strip()})).get("meals")
        if not meals:
            return self._empty_result()
        return {"meals": [self._meal_card(meal, include_area=True) for meal in meals[:limit]]}

    async def meals_by_ingredient(self, ingredient: str, limit: int = 12) -> dict[str, Any]:
        if not ingredient.strip():
            raise ValueError("ingredient must not be empty")
        if not 1 <= limit <= 25:
            raise ValueError("limit must be between 1 and 25")
        meals = (await self._get("filter.php", {"i": ingredient.strip()})).get("meals")
        if not meals:
            return self._empty_result()
        return {"meals": [self._meal_card(meal, include_area=False) for meal in meals[:limit]]}

    async def random_meal(self) -> dict[str, Any]:
        meals = (await self._get("random.php")).get("meals")
        if not meals:
            return self._empty_result()
        return self._meal_details(meals[0])

    async def meal_details(self, meal_id: str | int) -> dict[str, Any]:
        if not str(meal_id).strip():
            raise ValueError("id must not be empty")
        meals = (await self._get("lookup.php", {"i": str(meal_id).strip()})).get("meals")
        if not meals:
            return self._empty_result()
        return self._meal_details(meals[0])


mealdb = MealDBClient()


@mcp.tool()
async def search_meals_by_name(query: str, limit: int = 5) -> dict:
    """Search TheMealDB by meal name and return compact recipe cards."""
    return await mealdb.search_meals_by_name(query, limit)


@mcp.tool()
async def meals_by_ingredient(ingredient: str, limit: int = 12) -> dict:
    """Find TheMealDB meals that use the requested main ingredient."""
    return await mealdb.meals_by_ingredient(ingredient, limit)


@mcp.tool()
async def random_meal() -> dict:
    """Retrieve a random full recipe from TheMealDB."""
    return await mealdb.random_meal()


@mcp.tool()
async def meal_details(id: str | int) -> dict:
    """Retrieve a full recipe by TheMealDB meal ID."""
    return await mealdb.meal_details(id)


if __name__ == "__main__":
    mcp.run(transport="stdio")
