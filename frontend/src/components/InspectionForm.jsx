import { useState } from "react";
import api from "../api";

function InspectionForm({ onCreated }) {
  const [form, setForm] = useState({
    restaurantName: "",
    location: "",
    email: "",
    description: "",
    category: "",
  });

  const [message, setMessage] = useState("");

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");

    try {
      await api.post("/inspections/", form);

      setMessage("Inspection created successfully!");

      setForm({
        restaurantName: "",
        location: "",
        email: "",
        description: "",
        category: "",
      });

      onCreated();
    } catch (error) {
      console.error(error);
      setMessage("Could not create inspection.");
    }
  };

  return (
    <div>
      <h2>Add Inspection</h2>

      <form onSubmit={handleSubmit}>
        <input
          name="restaurantName"
          placeholder="Restaurant Name"
          value={form.restaurantName}
          onChange={handleChange}
          required
        />

        <input
          name="location"
          placeholder="Location"
          value={form.location}
          onChange={handleChange}
          required
        />

        <input
          name="email"
          type="email"
          placeholder="Email"
          value={form.email}
          onChange={handleChange}
          required
        />

        <input
          name="category"
          placeholder="Category"
          value={form.category}
          onChange={handleChange}
          required
        />

        <textarea
          name="description"
          placeholder="Description"
          value={form.description}
          onChange={handleChange}
          required
        />

        <button type="submit">Add Inspection</button>
      </form>

      {message && <p>{message}</p>}
    </div>
  );
}

export default InspectionForm;