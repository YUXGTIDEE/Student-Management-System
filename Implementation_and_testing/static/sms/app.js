(function () {
  "use strict";

  const storageKey = "sms-state-v1";
  const state = JSON.parse(localStorage.getItem(storageKey) || "{}");
  state.registrations = state.registrations || ["ENG1201-05"];
  state.locked = state.locked || {};

  function save() {
    localStorage.setItem(storageKey, JSON.stringify(state));
  }

  function toast(message, kind) {
    let el = document.querySelector(".toast");
    if (!el) {
      el = document.createElement("div");
      document.body.appendChild(el);
    }
    el.className = "toast " + (kind || "");
    el.textContent = message;
    clearTimeout(toast.timer);
    toast.timer = setTimeout(function () { el.remove(); }, 3200);
  }

  function notifySuccess(message) {
    toast(message, "ok");
  }

  function setupLogin() {
    const uid = document.querySelector("#uid");
    const pw = document.querySelector("#pw");
    const loginButton = document.querySelector(".auth .btn.pri");
    if (!uid || !pw || !loginButton) return;

    const error = Array.from(document.querySelectorAll(".notice")).find(function (el) {
      return el.classList.contains("bad");
    });
    if (error) error.hidden = true;

    loginButton.addEventListener("click", function (event) {
      event.preventDefault();
      const id = uid.value.trim();
      const validIds = ["SV2024001", "GV0457", "AD001"];
      const validPassword = "123456";

      if (!id || !pw.value || !validIds.includes(id.toUpperCase()) || pw.value !== validPassword) {
        if (error) error.hidden = false;
        return;
      }
      if (error) error.hidden = true;
      state.currentUser = id;
      state.role = id.toUpperCase().startsWith("AD") ? "admin" : id.toUpperCase().startsWith("GV") ? "teacher" : "student";
      save();
      const target = state.role === "admin"
        ? "../admin/A-Accounts.dc.html"
        : state.role === "teacher"
          ? "../teacher/T-Sections.dc.html"
          : "../student/S-Profile.dc.html";
      window.location.href = target;
    });

    [uid, pw].forEach(function (input) {
      input.addEventListener("input", function () {
        if (error) error.hidden = true;
      });
    });
  }

  function setupReset() {
    const input = document.querySelector("#rid");
    const button = Array.from(document.querySelectorAll("a.btn")).find(function (el) {
      return el.textContent.includes("Send reset");
    });
    if (!input || !button) return;
    const notices = document.querySelectorAll(".auth .notice");
    notices.forEach(function (notice) { notice.hidden = true; });
    input.addEventListener("input", function () {
      notices.forEach(function (notice) { notice.hidden = true; });
    });
    button.addEventListener("click", function (event) {
      event.preventDefault();
      const ok = Array.from(notices).find(function (el) { return el.classList.contains("ok"); });
      const bad = Array.from(notices).find(function (el) { return el.classList.contains("bad"); });
      notices.forEach(function (notice) { notice.hidden = true; });

      const value = input.value.trim().toLowerCase();
      const knownValues = [
        "sv2024001",
        "gv0457",
        "ad001",
        "an.nv@student.example.edu",
        "mai.tt@example.edu",
        "nam.lh@example.edu"
      ];
      if (knownValues.includes(value)) {
        if (ok) ok.hidden = false;
        notifySuccess("Reset instructions have been sent.");
        return;
      }
      if (bad) bad.hidden = false;
    });
  }

  function setupSearchFilters() {
    document.querySelectorAll('input[type="search"], input#q').forEach(function (input) {
      input.addEventListener("input", function () {
        const query = input.value.trim().toLowerCase();
        const table = input.closest("section, .card");
        if (!table) return;
        table.querySelectorAll("tbody tr").forEach(function (row) {
          row.hidden = !!query && !row.textContent.toLowerCase().includes(query);
        });
      });
    });
  }

  function setupOpenSections() {
    if (!document.title.includes("Open course sections")) return;
    const table = document.querySelector("table");
    if (!table) return;
    table.querySelectorAll("tbody tr").forEach(function (row) {
      const section = row.querySelector(".mono");
      if (!section) return;
      const code = section.textContent.trim();
      const action = row.querySelector("td:last-child");
      if (!action || state.registrations.includes(code)) return;
      const link = action.querySelector("a");
      if (link) {
        link.href = "../student/S-RegisterDialog.dc.html";
        link.addEventListener("click", function () {
          state.pendingSection = code;
          save();
        });
      }
    });
  }

  function setupRegistrationDialog() {
    if (!document.title.includes("Confirm registration")) return;
    const confirm = Array.from(document.querySelectorAll("a")).find(function (el) {
      return el.textContent.includes("Confirm registration");
    });
    if (!confirm) return;
    confirm.addEventListener("click", function (event) {
      event.preventDefault();
      const code = state.pendingSection || "INT2204-02";
      if (!state.registrations.includes(code)) state.registrations.push(code);
      save();
      notifySuccess("Registration confirmed.");
      window.location.href = "../student/S-Registered.dc.html";
    });
  }

  function setupRegistered() {
    if (!document.title.includes("Registered course")) return;
  }

  function setupCancellation() {
    if (!document.title.includes("Confirm cancellation")) return;
    const cancel = Array.from(document.querySelectorAll("a")).find(function (el) {
      return el.textContent.includes("Cancel registration");
    });
    if (!cancel) return;
    cancel.addEventListener("click", function (event) {
      event.preventDefault();
      state.registrations = state.registrations.filter(function (code) {
        return code !== "INT2301-01";
      });
      save();
      notifySuccess("Registration cancelled.");
      window.location.href = "../student/S-Registered.dc.html";
    });
  }

  function setupSaveLinks() {
    document.querySelectorAll("a.btn.pri").forEach(function (link) {
      const text = link.textContent.trim();
      if (text === "Save changes" || text === "Create account" || text === "Create section" || text === "Unlock gradebook") {
        link.addEventListener("click", function (event) {
          if (link.getAttribute("href") === "#") event.preventDefault();
          notifySuccess(text === "Unlock gradebook" ? "Gradebook unlocked." : "Changes saved.");
        });
      }
    });
  }

  function setupClearFilters() {
    document.querySelectorAll("a").forEach(function (link) {
      if (!["Clear filters", "Clear"].includes(link.textContent.trim())) return;
      link.addEventListener("click", function (event) {
        event.preventDefault();
        const card = link.closest("section, form, .main");
        if (!card) return;
        card.querySelectorAll("input, select").forEach(function (field) {
          if (field.tagName === "SELECT") field.selectedIndex = 0;
          else field.value = "";
        });
        card.querySelectorAll("tbody tr").forEach(function (row) { row.hidden = false; });
      });
    });
  }

  function setupGradebook() {
    if (!document.title.includes("Gradebook")) return;
    const inputs = Array.from(document.querySelectorAll("tbody input"));
    if (!inputs.length) return;

    function updateRow(row) {
      const values = Array.from(row.querySelectorAll("input")).map(function (input) {
        return Number(input.value);
      });
      const finalCell = row.cells[5];
      const letterCell = row.cells[6];
      const pointCell = row.cells[7];
      if (values.length !== 3 || values.some(function (value) { return !Number.isFinite(value) || value < 0 || value > 10; })) {
        finalCell.innerHTML = "&ndash;";
        letterCell.textContent = "\u2013";
        pointCell.textContent = "\u2013";
        row.querySelectorAll("input").forEach(function (input) {
          input.classList.toggle("bad", input.value !== "" && (!Number.isFinite(Number(input.value)) || Number(input.value) < 0 || Number(input.value) > 10));
        });
        return;
      }
      const finalGrade = values[0] * 0.10 + values[1] * 0.30 + values[2] * 0.60;
      const letter = finalGrade >= 8.5 ? "A" : finalGrade >= 7.0 ? "B" : finalGrade >= 5.5 ? "C" : finalGrade >= 4.0 ? "D" : "F";
      const points = letter === "A" ? 4 : letter === "B" ? 3 : letter === "C" ? 2 : letter === "D" ? 1 : 0;
      finalCell.innerHTML = "<b>" + finalGrade.toFixed(2) + "</b>";
      letterCell.textContent = letter;
      pointCell.textContent = points.toFixed(1);
    }

    inputs.forEach(function (input) {
      input.addEventListener("input", function () { updateRow(input.closest("tr")); });
    });

    const saveButton = Array.from(document.querySelectorAll("a.btn.pri")).find(function (el) {
      return el.textContent.includes("Save grades");
    });
    if (saveButton) {
      saveButton.addEventListener("click", function (event) {
        event.preventDefault();
        let invalid = false;
        document.querySelectorAll("tbody tr").forEach(function (row) {
          updateRow(row);
          if (row.querySelector(".bad")) invalid = true;
        });
        if (invalid) {
          toast("Correct invalid grades before saving.", "bad");
        } else {
          inputs.forEach(function (input) { state.locked[input.closest("tr").querySelector(".mono").textContent] = input.value; });
          save();
          notifySuccess("Grades saved.");
        }
      });
    }
  }

  function setupAccountActions() {
    if (!document.title.includes("Accounts")) return;
    document.querySelectorAll("tbody tr").forEach(function (row) {
      const status = row.querySelector(".chip");
      const actionLinks = Array.from(row.querySelectorAll("a"));
      actionLinks.forEach(function (link) {
        if (link.textContent.trim() === "Lock" || link.textContent.trim() === "Unlock" || link.textContent.trim() === "Activate") {
          link.href = "#";
          link.addEventListener("click", function (event) {
            event.preventDefault();
            if (link.classList.contains("off")) return;
            const action = link.textContent.trim();
            if (action === "Lock") {
              status.className = "chip bad";
              status.textContent = "Locked";
              link.textContent = "Unlock";
            } else if (action === "Unlock" || action === "Activate") {
              status.className = "chip ok";
              status.textContent = "Active";
              link.textContent = "Lock";
            }
            notifySuccess("Account status updated.");
          });
        }
      });
    });
  }

  function setupCourseActions() {
    if (!document.title.includes("Courses")) return;
    const form = document.querySelector("form.card");
    const addButton = form ? Array.from(form.querySelectorAll("a")).find(function (el) { return el.textContent.includes("Add course"); }) : null;
    if (form && addButton) {
      addButton.addEventListener("click", function (event) {
        event.preventDefault();
        const code = form.querySelector("#cc").value.trim();
        const name = form.querySelector("#cn").value.trim();
        if (!code || !name) {
          toast("Enter both course code and name.", "bad");
          return;
        }
        const tbody = document.querySelector("tbody");
        const row = tbody.insertRow();
        row.innerHTML = '<td class="mono">' + code.replace(/[<>&]/g, "") + '</td><td><b>' + name.replace(/[<>&]/g, "") + '</b></td><td>' + (form.querySelector("#cr").value || "3") + '</td><td>' + (form.querySelector("#cp").value || "45") + '</td><td><span class="row" style="gap:8px"><a class="btn sm" href="#">Update</a><a class="btn sm" href="#" style="color:var(--bad)">Delete</a></span></td>';
        form.reset();
        setupCourseRow(row);
        notifySuccess("Course added.");
      });
    }
    document.querySelectorAll("tbody tr").forEach(setupCourseRow);

    function setupCourseRow(row) {
      const deleteLink = Array.from(row.querySelectorAll("a")).find(function (el) { return el.textContent.includes("Delete"); });
      if (deleteLink) {
        deleteLink.addEventListener("click", function (event) {
          event.preventDefault();
          if (window.confirm("Delete this course?")) {
            row.remove();
            notifySuccess("Course deleted.");
          }
        });
      }
    }
  }

  function initialize() {
    setupLogin();
    setupReset();
    setupSearchFilters();
    setupOpenSections();
    setupRegistrationDialog();
    setupRegistered();
    setupCancellation();
    setupSaveLinks();
    setupGradebook();
    setupCourseActions();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize);
  } else {
    initialize();
  }
})();
