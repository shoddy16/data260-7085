import { useState } from "react";
import { useDispatch } from "react-redux";
import {
  deleteInspection,
  updateInspection,
} from "../features/inspections/inspectionsSlice";

function InspectionList({ inspections, restaurants }) {
  const dispatch = useDispatch();
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({
    restaurant_id: "",
    email: "",
    category: "",
    description: "",
    score: 100,
  });
  const [message, setMessage] = useState("");

  const startEdit = (inspection) => {
    setEditingId(inspection.id);
    setForm({
      restaurant_id: String(inspection.restaurant_id),
      email: inspection.email,
      category: inspection.category,
      description: inspection.description,
      score: inspection.score,
    });
    setMessage("");
  };

  const handleUpdate = async (id) => {
    const restaurant = restaurants.find((item) => item.id === Number(form.restaurant_id));
    if (!restaurant) {
      setMessage("Choose a restaurant for this inspection.");
      return;
    }
    try {
      await dispatch(updateInspection({
        id,
        payload: {
          restaurant_id: restaurant.id,
          restaurantName: restaurant.name,
          location: restaurant.location,
          email: form.email,
          category: form.category,
          description: form.description,
          score: Number(form.score),
        },
      })).unwrap();
      setEditingId(null);
      setMessage("Inspection updated.");
    } catch (error) {
      setMessage(String(error));
    }
  };

  const handleDelete = async (id) => {
    try {
      await dispatch(deleteInspection(id)).unwrap();
      setMessage("Inspection deleted.");
    } catch (error) {
      setMessage(String(error));
    }
  };

  if (inspections.length === 0) return <p>No inspections found.</p>;

  return (
    <div>
      {message ? <p role="status">{message}</p> : null}
      <ul className="entity-list inspection-list">
        {inspections.map((inspection) => {
          const restaurant = restaurants.find((item) => item.id === inspection.restaurant_id);
          const restaurantName = restaurant?.name || inspection.restaurantName;
          const location = restaurant?.location || inspection.location;
          return (
            <li key={inspection.id}>
              {editingId === inspection.id ? (
                <form className="entity-form edit-form" onSubmit={(event) => { event.preventDefault(); handleUpdate(inspection.id); }}>
                  <label>
                    Restaurant
                    <select value={form.restaurant_id} onChange={(event) => setForm({ ...form, restaurant_id: event.target.value })} required>
                      <option value="">Select a restaurant</option>
                      {restaurants.map((item) => <option key={item.id} value={item.id}>{item.name} — {item.location}</option>)}
                    </select>
                  </label>
                  <label>Contact email<input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} required /></label>
                  <label>Category<input value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} required /></label>
                  <label>Score<input type="number" min="0" max="100" value={form.score} onChange={(event) => setForm({ ...form, score: event.target.value })} required /></label>
                  <label>Description<textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} required /></label>
                  <div className="button-row">
                    <button type="submit">Save update</button>
                    <button type="button" onClick={() => setEditingId(null)}>Cancel</button>
                  </div>
                </form>
              ) : (
                <div className="inspection-card">
                  <div>
                    <h3>{restaurantName}</h3>
                    <p>Location: {location}</p>
                    <p>Inspection: {inspection.inspection_code} · Score: {inspection.score}</p>
                    <p>Email: {inspection.email}</p>
                    <p>Category: {inspection.category}</p>
                    <p>{inspection.description}</p>
                  </div>
                  <div className="button-row">
                    <button type="button" onClick={() => startEdit(inspection)}>Update</button>
                    <button type="button" onClick={() => handleDelete(inspection.id)}>Delete</button>
                  </div>
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default InspectionList;
