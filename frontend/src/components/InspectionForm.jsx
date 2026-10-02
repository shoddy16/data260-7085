import { useState } from "react";
import { useDispatch } from "react-redux";
import { createInspection } from "../features/inspections/inspectionsSlice";

const emptyForm = {
  restaurant_id: "",
  email: "",
  category: "",
  description: "",
  score: 100,
};

function InspectionForm({ restaurants }) {
  const dispatch = useDispatch();
  const [form, setForm] = useState(emptyForm);
  const [message, setMessage] = useState("");

  const selectedRestaurant = restaurants.find(
    (restaurant) => restaurant.id === Number(form.restaurant_id),
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");
    if (!selectedRestaurant) {
      setMessage("Choose a restaurant before creating an inspection.");
      return;
    }
    const payload = {
      restaurant_id: selectedRestaurant.id,
      restaurantName: selectedRestaurant.name,
      location: selectedRestaurant.location,
      email: form.email,
      category: form.category,
      description: form.description,
      score: Number(form.score),
    };
    try {
      await dispatch(createInspection(payload)).unwrap();
      setMessage("Inspection created.");
      setForm(emptyForm);
    } catch (error) {
      setMessage(String(error));
    }
  };

  return (
    <form className="entity-form" onSubmit={handleSubmit}>
      <label>
        Restaurant
        <select value={form.restaurant_id} onChange={(event) => setForm({ ...form, restaurant_id: event.target.value })} required>
          <option value="">Select a restaurant</option>
          {restaurants.map((restaurant) => (
            <option key={restaurant.id} value={restaurant.id}>{restaurant.name} — {restaurant.location}</option>
          ))}
        </select>
      </label>
      <label>
        Contact email
        <input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required maxLength={255} />
      </label>
      <label>
        Inspection category
        <input value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} required maxLength={100} />
      </label>
      <label>
        Score (0–100)
        <input type="number" min="0" max="100" value={form.score} onChange={(event) => setForm({ ...form, score: event.target.value })} required />
      </label>
      <label>
        Description
        <textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} required />
      </label>
      <button type="submit" disabled={restaurants.length === 0}>Add inspection</button>
      {restaurants.length === 0 ? <p>Add a restaurant first.</p> : null}
      {message ? <p role="status">{message}</p> : null}
    </form>
  );
}

export default InspectionForm;
