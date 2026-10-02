import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import api from "../api";
import { fetchInspections } from "../features/inspections/inspectionsSlice";
import { fetchRestaurants } from "../features/restaurants/restaurantsSlice";
import InspectionForm from "./InspectionForm";
import InspectionList from "./InspectionList";
import RestaurantManager from "./RestaurantManager";

function Dashboard() {
  const dispatch = useDispatch();
  const inspections = useSelector((state) => state.inspections.items);
  const inspectionState = useSelector((state) => state.inspections);
  const restaurants = useSelector((state) => state.restaurants.items);
  const restaurantState = useSelector((state) => state.restaurants);

  useEffect(() => {
    dispatch(fetchRestaurants());
    dispatch(fetchInspections());
  }, [dispatch]);

  const handleLogout = async () => {
    try {
      await api.post("/logout");
      window.location.href = "/login";
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">DATA 260 · HW5</p>
          <h1>Restaurant Inspection Dashboard</h1>
          <p>Manage restaurants and their inspection history.</p>
        </div>
        <button type="button" onClick={handleLogout}>Logout</button>
      </header>

      {(inspectionState.error || restaurantState.error) && (
        <p className="error-message" role="alert">
          {inspectionState.error || restaurantState.error}
        </p>
      )}

      <section className="panel">
        <h2>Restaurants</h2>
        <RestaurantManager restaurants={restaurants} />
      </section>

      <section className="panel">
        <h2>Create an inspection</h2>
        <InspectionForm restaurants={restaurants} />
      </section>

      <section className="panel">
        <h2>Inspection records</h2>
        {inspectionState.loading ? <p>Loading inspections…</p> : null}
        <InspectionList inspections={inspections} restaurants={restaurants} />
      </section>
    </main>
  );
}

export default Dashboard;
