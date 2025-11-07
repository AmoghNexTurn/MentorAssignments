// const API_URL = "https://bxswk4gl-5000.inc1.devtunnels.ms/submit"; // Change to your Flask endpoint
const API_URL = "http://127.0.0.1:5000/submit";

async function postData(operation, data) {
    data.operation = operation;
    const res = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
    });
    console.log(res.json);
    return res.json();
}

function formatForHTML(text) {
  return text
    .replace(/"/g, '')        // remove all double quotes
    .replace(/\\n/g, '<br>')  // handle literal "\n"
    .replace(/\n/g, '<br>');  // handle real newlines
}

// ---------- 1. Create User ----------
const addUserForm = document.getElementById("addUserForm");
if (addUserForm) {
    addUserForm.addEventListener("submit", async e => {
        e.preventDefault();
        const formData = Object.fromEntries(new FormData(addUserForm));
        if (formData["AvailableHours"].trim() === "") {
            delete formData["AvailableHours"];
        }

        const res = await postData("add_user", formData);
        const apiResponse = document.getElementById("apiResponse");
        if (apiResponse) {
            apiResponse.innerHTML = formatForHTML(JSON.stringify(res, null, 2));
        }
    });
}

// ---------- 2. Get Info ----------
const getInfoForm = document.getElementById("getInfoForm");
if (getInfoForm) {
    getInfoForm.addEventListener("submit", async e => {
        e.preventDefault();
        const formData = Object.fromEntries(new FormData(getInfoForm));
        const res = await postData("get_info", formData);
        const apiResponse = document.getElementById("apiResponse");
        if (apiResponse) {
            apiResponse.innerHTML = formatForHTML(JSON.stringify(res, null, 2));
        }
    });
}

// ---------- 3. Add Booking ----------
const addBookingForm = document.getElementById("addBookingForm");
if (addBookingForm) {
    addBookingForm.addEventListener("submit", async e => {
        e.preventDefault();
        const formData = Object.fromEntries(new FormData(addBookingForm));
        // Try to parse HoursBooked if JSON-like string
        try {
            formData.HoursBooked = JSON.parse(formData.HoursBooked);
        } catch {
            // leave as string if parse fails
        }
        const res = await postData("add_booking", formData);
        const apiResponse = document.getElementById("apiResponse");
        if (apiResponse) {
            apiResponse.innerHTML = formatForHTML(JSON.stringify(res, null, 2));
        }
    });
}

// ---------- 4. Add Bid ----------
const addBidForm = document.getElementById("addBidForm");
if (addBidForm) {
    addBidForm.addEventListener("submit", async e => {
        e.preventDefault();
        const formData = Object.fromEntries(new FormData(addBidForm));
        try {
            formData.HoursBooked = JSON.parse(formData.HoursBooked);
        } catch {
            // leave as string
        }
        const res = await postData("add_bid", formData);
        const apiResponse = document.getElementById("apiResponse");
        if (apiResponse) {
            apiResponse.innerHTML = formatForHTML(JSON.stringify(res, null, 2));
        }
    });
}

// ---------- 5. Check Availability ----------
const checkAvailabilityForm = document.getElementById("checkAvailabilityForm");
if (checkAvailabilityForm) {
    checkAvailabilityForm.addEventListener("submit", async e => {
        e.preventDefault();
        const formData = Object.fromEntries(new FormData(checkAvailabilityForm));
        try {
            formData.HoursBooked = JSON.parse(formData.HoursBooked);
        } catch {
            // leave as string
        }
        const res = await postData("check_availability", formData);
        const apiResponse = document.getElementById("apiResponse");
        if (apiResponse) {
            apiResponse.innerHTML = formatForHTML(JSON.stringify(res, null, 2));
        }
    });
}

// ---------- 6. Choose Bid ----------
const chooseBidForm = document.getElementById("chooseBidForm");
if (chooseBidForm) {
    chooseBidForm.addEventListener("submit", async e => {
        e.preventDefault();
        const formData = Object.fromEntries(new FormData(chooseBidForm));
        const res = await postData("choose_bid", formData);
        const apiResponse = document.getElementById("apiResponse");
        if (apiResponse) {
            apiResponse.innerHTML = formatForHTML(JSON.stringify(res, null, 2));
        }
    });
}
