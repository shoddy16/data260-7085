"use strict";


const submissionCounter = (() => {
    let count = 0;

    return () => {
        count++;
        return count;
    };
})();


// we use the arrow fnc here
const validateForm = () => {
    const description = document.getElementById("description").value.trim();
    const terms = document.getElementById("terms").checked;

    // The description must contain more than 25 characters.
    if (description.length <= 25) {
        alert("Inspection description must be more than 25 characters.");
        return false;
    }

    // The terms and conditions checkbox must be checked.
    if (!terms) {
        alert("Please agree to the terms and conditions.");
        return false;
    }

    return true;
};



document.getElementById("inspectionForm").addEventListener("submit", (event) => {
    event.preventDefault();

    
    if (!validateForm()) {
        return;
    }

    
    const restaurantName = document.getElementById("restaurantName").value.trim();
    const location = document.getElementById("location").value.trim();
    const email = document.getElementById("email").value.trim();
    const description = document.getElementById("description").value.trim();
    const category = document.getElementById("category").value;

    
    const inspectionData = {
        restaurantName,
        location,
        email,
        description,
        category
    };

    // We convert the object into a JSON string
    const jsonString = JSON.stringify(inspectionData);
    console.log("Form Data as JSON String:", jsonString);

    // We again convert the JSON string back into an object
    const parsedData = JSON.parse(jsonString);
    console.log("Parsed JSON Object:", parsedData);


    // we will now extract the primary field and email
    const {
        restaurantName: submittedRestaurant,
        email: submitterEmail
    } = parsedData;

    console.log("Restaurant Name:", submittedRestaurant);
    console.log("Submitter Email:", submitterEmail);


    // we add current date and time
    const updatedData = {
        ...parsedData,
        submissionDate: new Date().toISOString()
    };

    console.log("Updated Inspection Data:", updatedData);


    
    const submissionCount = submissionCounter();

    console.log("Successful Submission Count:", submissionCount);

    alert("Inspection submitted successfully!");

    
    document.getElementById("inspectionForm").reset();
});