(function () {
  "use strict";

  const board = document.querySelector("[data-board]");
  if (!board) return;

  let draggedCard = null;
  let sourceColumn = null;

  function updateColumn(column) {
    const cards = column.querySelectorAll("[data-issue-key]");
    column.querySelector("[data-column-count]").textContent = cards.length;
    column.classList.toggle("is-empty", cards.length === 0);
  }

  function updateAllColumns() {
    board.querySelectorAll("[data-status]").forEach(updateColumn);
  }

  board.addEventListener("dragstart", function (event) {
    const card = event.target.closest("[data-issue-key]");
    if (!card) return;
    draggedCard = card;
    sourceColumn = card.closest("[data-status]");
    card.classList.add("dragging");
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", card.dataset.issueKey);
  });

  board.addEventListener("dragend", function () {
    if (draggedCard) draggedCard.classList.remove("dragging");
    board.querySelectorAll(".drag-over").forEach((el) => el.classList.remove("drag-over"));
  });

  board.addEventListener("dragover", function (event) {
    const column = event.target.closest("[data-status]");
    if (!column || !draggedCard) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    board.querySelectorAll(".drag-over").forEach((el) => el !== column && el.classList.remove("drag-over"));
    column.classList.add("drag-over");
  });

  board.addEventListener("dragleave", function (event) {
    const column = event.target.closest("[data-status]");
    if (column && !column.contains(event.relatedTarget)) {
      column.classList.remove("drag-over");
    }
  });

  board.addEventListener("drop", async function (event) {
    const targetColumn = event.target.closest("[data-status]");
    if (!targetColumn || !draggedCard) return;
    event.preventDefault();
    targetColumn.classList.remove("drag-over");

    const card = draggedCard;
    const fromColumn = sourceColumn;
    draggedCard = null;
    sourceColumn = null;

    if (targetColumn === fromColumn) return;

    const newStatus = targetColumn.dataset.status;
    targetColumn.querySelector("[data-column-cards]").appendChild(card);
    updateAllColumns();
    card.classList.add("saving");

    try {
      await window.TaskFlow.apiRequest(
        "POST",
        `/api/v1/issues/${encodeURIComponent(card.dataset.issueKey)}/transition`,
        { status: newStatus }
      );
      card.dataset.currentStatus = newStatus;
      window.TaskFlow.toast(`${card.dataset.issueKey} moved to ${targetColumn.dataset.statusLabel}`);
    } catch (error) {
      fromColumn.querySelector("[data-column-cards]").appendChild(card);
      updateAllColumns();
      window.TaskFlow.toast(error.message, "error");
    } finally {
      card.classList.remove("saving");
    }
  });

  updateAllColumns();
})();
