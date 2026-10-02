import { useState } from "react";
import { useDispatch } from "react-redux";
import {
  createRestaurant,
  deleteRestaurant,
  updateRestaurant,
} from "../features/restaurants/restaurantsSlice";

const emptyForm = { name: "", location: "", code: "" };

function RestaurantManager({ restaurants }) {
  const dispatch = useDispatch();
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [message, setMessage] = useState("");

  const beginEdit = (restaurant) => {
    setEditingId(restaurant.id);
    setForm({ name: restaurant.name, location: restaurant.location, code: restaurant.code });
    setMessage("");
  };

  const cancelEdit = () => {
    setEditingId(null);
    setForm(emptyForm);
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMessage("");
    const payload = { name: form.name, location: form.location };
    if (form.code) payload.code = form.code;
    try {
      if (editingId) {
        await dispatch(updateRestaurant({ id: editingId, payload })).unwrap();
        setMessage("Restaurant updated.");
      } else {
        await dispatch(createRestaurant(payload)).unwrap();
        setMessage("Restaurant created.");
      }
      cancelEdit();
    } catch (error) {
      setMessage(String(error));
    }
  };

  const handleDelete = async (id) => {
    setMessage("");
    try {
      await dispatch(deleteRestaurant(id)).unwrap();
      setMessage("Restaurant deleted.");
    } catch (error) {
      setMessage(String(error));
    }
  };

  return (
    <div className="entity-manager">
      <form className="entity-form" onSubmit={handleSubmit}>
        <label>
          Restaurant name
          <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required maxLength={255} />
        </label>
        <label>
          Location
          <input value={form.location} onChange={(event) => setForm({ ...form, location: event.target.value })} required maxLength={500} />
        </label>
        <label>
          Restaurant code (optional)
          <input value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })} placeholder="Generated when blank" pattern="s7085-r-[a-f0-9]{8}" />
        </label>
        <div className="button-row">
          <button type="submit">{editingId ? "Save restaurant" : "Add restaurant"}</button>
          {editingId ? <button type="button" onClick={cancelEdit}>Cancel</button> : null}
        </div>
      </form>

      {message ? <p role="status">{message}</p> : null}

      {restaurants.length === 0 ? <p>No restaurants yet.</p> : (
        <ul className="entity-list">
          {restaurants.map((restaurant) => (
            <li key={restaurant.id}>
              <div>
                <strong>{restaurant.name}</strong>
                <span>{restaurant.location}</span>
                <small>{restaurant.code}</small>
              </div>
              <div className="button-row">
                <button type="button" onClick={() => beginEdit(restaurant)}>Edit</button>
                <button type="button" onClick={() => handleDelete(restaurant.id)}>Delete</button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default RestaurantManager;
