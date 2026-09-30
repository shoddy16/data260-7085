import { useEffect, useState } from "react";
import api from "../api";
import InspectionList from "./InspectionList";
import InspectionForm from "./InspectionForm";

function Dashboard() {
  const [inspections, setInspections] = useState([]);
  const [message, setMessage] = useState("");

  const loadInspections = async () => {
    try {
      const response = await api.get("/inspections/");
      setInspections(response.data);
      setMessage("");
    } catch (error) {
      console.error(error);
      setMessage("Could not load inspections.");
    }
  };

  useEffect(() => {
    loadInspections();
  }, []);

  const handleLogout = async () => {
    try {
      await api.post("/logout");
      window.location.href = "/login";
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <h1>Inspection Dashboard</h1>

      <button onClick={handleLogout}>Logout</button>

      {message && <p>{message}</p>}

      <InspectionForm onCreated={loadInspections} />

      <InspectionList
        inspections={inspections}
        onChanged={loadInspections}
      />
    </div>
  );
}

export default Dashboard;