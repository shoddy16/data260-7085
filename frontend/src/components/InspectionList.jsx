import { useState } from "react";
import api from "../api";

function InspectionList({ inspections, onChanged }) {
  const [editingId, setEditingId] = useState(null);
  const [form, setForm] = useState({
    restaurantName: "",
    location: "",
    email: "",
    category: "",
    description: "",
  });

  const startEdit = (inspection) => {
    setEditingId(inspection.id);
    setForm({
      restaurantName: inspection.restaurantName,
      location: inspection.location,
      email: inspection.email,
      category: inspection.category,
      description: inspection.description,
    });
  };

  const handleUpdate = async (id) => {
    try {
      await api.put(`/inspections/${id}`, form);
      setEditingId(null);
      onChanged();
    } catch (err) {
      console.error(err);
      alert("Could not update inspection.");
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/inspections/${id}`);
      onChanged();
    } catch (err) {
      console.error(err);
      alert("Could not delete inspection.");
    }
  };

  return (
    <div>
      <h2>Inspections</h2>

      {inspections.length === 0 ? (
        <p>No inspections found.</p>
      ) : (
        inspections.map((inspection) => (
          <div key={inspection.id}>
            {editingId === inspection.id ? (
              <div>
                <input
                  value={form.restaurantName}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      restaurantName: e.target.value,
                    })
                  }
                />

                <input
                  value={form.location}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      location: e.target.value,
                    })
                  }
                />

                <input
                  value={form.email}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      email: e.target.value,
                    })
                  }
                />

                <input
                  value={form.category}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      category: e.target.value,
                    })
                  }
                />

                <textarea
                  value={form.description}
                  onChange={(e) =>
                    setForm({
                      ...form,
                      description: e.target.value,
                    })
                  }
                />

                <button onClick={() => handleUpdate(inspection.id)}>
                  Save Update
                </button>

                <button onClick={() => setEditingId(null)}>
                  Cancel
                </button>
              </div>
            ) : (
              <div>
                <h3>{inspection.restaurantName}</h3>
                <p>Location: {inspection.location}</p>
                <p>Email: {inspection.email}</p>
                <p>Category: {inspection.category}</p>
                <p>{inspection.description}</p>

                <button onClick={() => startEdit(inspection)}>
                  Update
                </button>

                <button onClick={() => handleDelete(inspection.id)}>
                  Delete
                </button>
              </div>
            )}
          </div>
        ))
      )}
    </div>
  );
}

export default InspectionList;