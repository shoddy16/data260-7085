"use strict";

const form = document.getElementById("inspectionForm");
const inspectionList = document.getElementById("inspectionList");
const loadingState = document.getElementById("loadingState");
const emptyState = document.getElementById("emptyState");
const errorState = document.getElementById("errorState");
const searchInput = document.getElementById("searchInput");
const searchButton = document.getElementById("searchButton");
const clearSearchButton = document.getElementById("clearSearchButton");
const updateButton = document.getElementById("updateButton");
const deleteButton = document.getElementById("deleteButton");

const showState = (state) => {
    loadingState.classList.add("hidden");
    emptyState.classList.add("hidden");
    errorState.classList.add("hidden");
    inspectionList.classList.add("hidden");

    if (state === "loading") {
        loadingState.classList.remove("hidden");
    } else if (state === "empty") {
        emptyState.classList.remove("hidden");
    } else if (state === "error") {
        errorState.classList.remove("hidden");
    } else if (state === "list") {
        inspectionList.classList.remove("hidden");
    }
};

const displayInspections = (inspections) => {
    if (inspections.length === 0) {
        showState("empty");
        return;
    }

    inspectionList.innerHTML = inspections.map((inspection) => `
        <div class="inspection-card">
            <h3>${inspection.restaurantName}</h3>
            <p><strong>Location:</strong> ${inspection.location}</p>
            <p><strong>Email:</strong> ${inspection.email}</p>
            <p><strong>Description:</strong> ${inspection.description}</p>
            <p><strong>Category:</strong> ${inspection.category}</p>
            <p><strong>ID:</strong> ${inspection.id}</p>
        </div>
    `).join("");

    showState("list");
};

const loadInspections = async (search = "") => {
    showState("loading");

    try {
        const url = search
            ? `/api/inspections?search=${encodeURIComponent(search)}`
            : "/api/inspections";

        const response = await fetch(url);

        if (!response.ok) {
            throw new Error("Unable to load inspections");
        }

        const inspections = await response.json();
        displayInspections(inspections);
    } catch (error) {
        console.error(error);
        showState("error");
    }
};

const validateForm = () => {
    const description = document.getElementById("description").value.trim();
    const terms = document.getElementById("terms").checked;

    if (description.length <= 25) {
        alert("Inspection description must be more than 25 characters.");
        return false;
    }

    if (!terms) {
        alert("Please agree to the terms and conditions.");
        return false;
    }

    return true;
};

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!validateForm()) {
        return;
    }

    const inspectionData = {
        restaurantName: document.getElementById("restaurantName").value.trim(),
        location: document.getElementById("location").value.trim(),
        email: document.getElementById("email").value.trim(),
        description: document.getElementById("description").value.trim(),
        category: document.getElementById("category").value
    };

    try {
        const response = await fetch("/api/inspections", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(inspectionData)
        });

        if (!response.ok) {
            throw new Error("Unable to submit inspection");
        }

        alert("Inspection submitted successfully!");
        form.reset();
        window.location.href = "/";
    } catch (error) {
        console.error(error);
        alert("Unable to submit inspection.");
    }
});

searchButton.addEventListener("click", () => {
    loadInspections(searchInput.value.trim());
});

searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        loadInspections(searchInput.value.trim());
    }
});

clearSearchButton.addEventListener("click", () => {
    searchInput.value = "";
    loadInspections();
});

updateButton.addEventListener("click", async () => {
    const updatedInspection = {
        restaurantName: "Updated Spice House",
        location: "Santa Clara",
        email: "updated@example.com",
        description: "Updated inspection findings after a follow-up restaurant inspection.",
        category: "Conditional Pass"
    };

    try {
        const response = await fetch("/api/inspections/1", {
            method: "PUT",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(updatedInspection)
        });

        if (!response.ok) {
            throw new Error("Unable to update inspection");
        }

        alert("Inspection ID 1 updated successfully!");
        window.location.href = "/";
    } catch (error) {
        console.error(error);
        alert("Unable to update inspection.");
    }
});

deleteButton.addEventListener("click", async () => {
    try {
        const response = await fetch("/api/inspections");
        const inspections = await response.json();

        if (inspections.length === 0) {
            alert("No inspections to delete.");
            return;
        }

        const highestId = Math.max(
            ...inspections.map((inspection) => inspection.id)
        );

        const deleteResponse = await fetch(
            `/api/inspections/${highestId}`,
            {
                method: "DELETE"
            }
        );

        if (!deleteResponse.ok) {
            throw new Error("Unable to delete inspection");
        }

        alert(`Inspection ID ${highestId} deleted successfully!`);
        window.location.href = "/";
    } catch (error) {
        console.error(error);
        alert("Unable to delete inspection.");
    }
});

loadInspections();