// -------------------- Page Load Logic --------------------

/**
 * On DOM load, if the confirmed SQL textarea is not empty,
 * display the generated SQL container so the user can see the query.
 */
window.addEventListener("DOMContentLoaded", () => {
  const sqlTextarea = document.querySelector('textarea[name="confirmed_sql"]');
  const sqlContainer = document.getElementById("generated-sql-container");
  if (sqlTextarea && sqlTextarea.value.trim() !== "") {
    sqlContainer.style.display = "block";
  }
});

// -------------------- History Item Click Handling --------------------

/**
 * When a history text link in the sidebar is clicked:
 * - Fetch the corresponding history item from the server
 * - Populate the question textarea and SQL textarea
 * - Update the database selection in both navbar and hidden fields
 */
document.querySelectorAll(".sidebar-item").forEach((item) => {
  item.querySelector(".history-text")?.addEventListener("click", async (e) => {
    e.preventDefault();

    const db = item.getAttribute("data-db");
    const id = item.getAttribute("data-id");
    if (!db || !id) return;

    try {
      const res = await fetch(`/history_item/${encodeURIComponent(db)}/${id}`);
      const data = await res.json();

      if (data.status === "success") {
        const questionTextarea = document.getElementById("question");
        const sqlTextarea = document.querySelector(
          'textarea[name="confirmed_sql"]'
        );
        const sqlContainer = document.getElementById("generated-sql-container");

        if (questionTextarea) {
          questionTextarea.value = data.question;
          questionTextarea.style.height = "auto";
          questionTextarea.style.height = questionTextarea.scrollHeight + "px";
          questionTextarea.focus();
        }

        if (sqlTextarea && sqlContainer) {
          sqlTextarea.value = data.generated_sql;
          sqlContainer.style.display = "block";
        }

        // Update hidden inputs and navbar database selection
        const hiddenDbInput = document.getElementById("database-hidden");
        if (hiddenDbInput) hiddenDbInput.value = db;

        const navbarSelect = document.getElementById("database");
        if (navbarSelect) navbarSelect.value = db;

        const confirmDbInput = document.querySelector('input[name="database"]');
        if (confirmDbInput) confirmDbInput.value = db;

        const confirmQuestionInput = document.querySelector(
          'input[name="question"]'
        );
        if (confirmQuestionInput) confirmQuestionInput.value = data.question;
      } else {
        alert(
          "Failed to load history item: " + (data.message || "Unknown error")
        );
      }
    } catch (error) {
      alert("Error loading history item: " + error.message);
    }
  });
});

// -------------------- Hide SQL Container on New Input --------------------

/**
 * While typing a new question manually, hide the generated SQL container
 * until the new query is submitted.
 */
// const questionTextarea = document.getElementById("question");
// const sqlContainer = document.getElementById("generated-sql-container");

// questionTextarea.addEventListener("input", () => {
//   if (sqlContainer) {
//     sqlContainer.style.display = "none";
//   }
// });

// -------------------- Loader Display --------------------

/**
 * Show a loader animation or element during form submission.
 */
function showLoader() {
  document.getElementById("loader").style.display = "block";
}

// -------------------- Confirm Form Submission --------------------

/**
 * Handle the confirmation form submission via AJAX:
 * - Send data to server
 * - Show success or error toast notifications based on server response
 */
document.getElementById("thumbUp").addEventListener("click", async () => {
  await submitFeedback("yes");
});
document.getElementById("thumbDown").addEventListener("click", async () => {
  await submitFeedback("no");
});

async function submitFeedback(value) {
  const form = document.getElementById("confirmForm");
  const isCorrectInput = document.getElementById("is_correct");
  isCorrectInput.value = value;

  const formData = new FormData(form);
  const res = await fetch("/confirm", { method: "POST", body: formData });
  const result = await res.json();

  if (result.status === "success") {
    document.getElementById("toastMessage").textContent =
      "Query saved successfully.";
    const toast = new bootstrap.Toast(document.getElementById("feedbackToast"));
    toast.show();
  } else if (result.status === "ignored") {
    document.getElementById("toastErrorMessage").textContent =
      "Query not saved.";
    const toast = new bootstrap.Toast(
      document.getElementById("feedbackErrorToast")
    );
    toast.show();
  } else {
    document.getElementById("toastErrorMessage").textContent =
      "Error: " + result.message;
    const toast = new bootstrap.Toast(
      document.getElementById("feedbackErrorToast")
    );
    toast.show();
  }
}

// -------------------- Delete History --------------------

/**
 * Delete a history item from the server (page reload after success).
 * @param {string} dbName - Database name
 * @param {string} id - History record ID
 */
function deleteHistory(dbName, id) {
  if (!confirm("Are you sure you want to delete this history item?")) return;

  fetch(`/delete_history/${encodeURIComponent(dbName)}/${id}`, {
    method: "POST",
  })
    .then((res) => {
      if (res.ok) location.reload();
      else alert("Failed to delete history.");
    })
    .catch((err) => console.error(err));
}

/**
 * Delete a history item from the server without page reload.
 * Removes the item from the sidebar list on success.
 * @param {string} db - Database name
 * @param {string} id - History record ID
 */
async function deleteHistoryItem(db, id) {
  if (!confirm("Are you sure you want to delete this history item?")) return;

  try {
    const response = await fetch(`/delete_history/${db}/${id}`, {
      method: "POST",
    });
    const data = await response.json();

    if (data.status === "success") {
      const li = document.querySelector(`li[data-id='${id}'][data-db='${db}']`);
      if (li) li.remove();
    } else {
      alert("Delete failed: " + (data.message || "Unknown error"));
    }
  } catch (err) {
    alert("Error deleting item: " + err);
  }
}

// -------------------- Textarea Auto-Resize --------------------

/**
 * Auto-resize the question textarea while typing.
 * Restricts height to a maximum of ~2 lines.
 * Enter key submits the form, Shift+Enter adds a new line.
 */
const textarea = document.getElementById("question");
const form = document.getElementById("chat-form");

// Auto-resize function
function autoResize() {
  textarea.style.height = "auto"; // reset height
  const scrollHeight = textarea.scrollHeight;
  const lineHeight = parseFloat(getComputedStyle(textarea).lineHeight);
  const maxHeight = lineHeight * 6 + 16; // limit to ~6 lines

  if (scrollHeight > maxHeight) {
    textarea.style.height = maxHeight + "px";
    textarea.scrollTop = textarea.scrollHeight; // allow scrolling within max height
  } else {
    textarea.style.height = scrollHeight + "px";
  }
}

// Event listeners
textarea.addEventListener("input", autoResize);
window.addEventListener("DOMContentLoaded", autoResize);

// Enter/Shift+Enter behavior
textarea.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault(); // prevent new line
    form.requestSubmit(); // submit the form
  }
});

// -------------------- Database Dropdown Sync --------------------

/**
 * Sync hidden form input value with the database selection in the navbar.
 * Ensures correct DB name is sent with form submissions.
 */
const navbarSelect = document.getElementById("database");
const hiddenInput = document.getElementById("database-hidden");

navbarSelect.addEventListener("change", () => {
  hiddenInput.value = navbarSelect.value;
});

window.addEventListener("DOMContentLoaded", () => {
  hiddenInput.value = navbarSelect.value;
});

/**
 * Copy database dropdown value into hidden input before form submit.
 */
function copyDatabaseValue() {
  hiddenInput.value = navbarSelect.value;
}

// -------------------- Sidebar Item Click Active State --------------------

/**
 * Add active class to clicked sidebar item and fetch its details.
 */
document.addEventListener("DOMContentLoaded", function () {
  const items = document.querySelectorAll(".sidebar-item");

  items.forEach((item) => {
    item.addEventListener("click", function () {
      items.forEach((el) => el.classList.remove("active"));
      this.classList.add("active");

      const historyId = this.dataset.id;
      const dbName = this.dataset.db;
      fetch(`/history_item/${dbName}/${historyId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.status === "success") {
            document.querySelector("#question").value = data.question;
            document.querySelector("#sql").value = data.generated_sql;
          }
        });
    });
  });
});

// -------------------- New Query Button Logic --------------------
document.getElementById("newQueryBtn").addEventListener("click", () => {
  // Clear the main textarea
  const questionTextarea = document.getElementById("question");
  if (questionTextarea) questionTextarea.value = "";

  // Clear the SQL textarea
  const sqlTextarea = document.querySelector(".custom-textarea");
  if (sqlTextarea) sqlTextarea.value = "";

  // Clear any hidden inputs (optional)
  const hiddenInputs = document.querySelectorAll("input[type='hidden']");
  hiddenInputs.forEach((input) => (input.value = ""));

  // Optionally clear generated SQL container
  const sqlContainer = document.getElementById("generated-sql-container");
  if (sqlContainer) sqlContainer.style.display = "none";

  // Reload the page if you really want a fresh start
  location.reload();
});

// -------------------- Auto Resize for SQL textarea (no max height, expands fully) --------------------
document.addEventListener("DOMContentLoaded", () => {
  const textareas = document.querySelectorAll(".custom-textarea");

  textareas.forEach((textarea) => {
    const autoResize = () => {
      textarea.style.height = "auto"; // reset height
      textarea.style.height = textarea.scrollHeight + "px"; // set height to content
    };

    // Resize on input
    textarea.addEventListener("input", autoResize);

    // Initial resize on page load
    autoResize();
  });
});

// -------------------- Copy to Clipboard for SQL textarea --------------------
const copyBtn = document.getElementById("copyBtn");
const sqlTextareaCopy = document.getElementById("sqlTextarea");

if (copyBtn && sqlTextareaCopy) {
  copyBtn.addEventListener("click", () => {
    sqlTextareaCopy.select();
    sqlTextareaCopy.setSelectionRange(0, 99999); // For mobile

    try {
      const successful = document.execCommand("copy");
      if (successful) {
        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied';
        setTimeout(() => {
          copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
        }, 1500);
      } else {
        alert("Failed to copy");
      }
    } catch (err) {
      alert("Copy command is not supported in your browser.");
    }
    window.getSelection().removeAllRanges();
  });
}

const thumbUp = document.getElementById("thumbUp");
const thumbDown = document.getElementById("thumbDown");

function addPopEffect(element) {
  element.classList.add("pop");
  setTimeout(() => element.classList.remove("pop"), 300);
}

thumbUp.addEventListener("click", function () {
  const icon = this.querySelector("i");
  if (icon.classList.contains("bi-hand-thumbs-up")) {
    icon.classList.replace("bi-hand-thumbs-up", "bi-hand-thumbs-up-fill");
    this.classList.add("active");
  } else {
    icon.classList.replace("bi-hand-thumbs-up-fill", "bi-hand-thumbs-up");
    this.classList.remove("active");
  }
  addPopEffect(this);
});

thumbDown.addEventListener("click", function () {
  const icon = this.querySelector("i");
  if (icon.classList.contains("bi-hand-thumbs-down")) {
    icon.classList.replace("bi-hand-thumbs-down", "bi-hand-thumbs-down-fill");
    this.classList.add("active");
  } else {
    icon.classList.replace("bi-hand-thumbs-down-fill", "bi-hand-thumbs-down");
    this.classList.remove("active");
  }
  addPopEffect(this);
});
