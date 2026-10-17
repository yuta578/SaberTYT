/* ==========================================================================
   SIMULADOR DE CUESTIONARIOS SABER TyT - ROBUST EXAM ENGINE JS
   ========================================================================== */

class SimulacroEngine {
  constructor(config) {
    this.totalQuestions = (config && config.totalQuestions) ? parseInt(config.totalQuestions, 10) : 5;
    this.timeLimitMinutes = (config && config.timeLimitMinutes) ? parseInt(config.timeLimitMinutes, 10) : 45;
    this.currentQuestionIndex = 0;
    this.answers = {}; // { questionIndex: selectedOptionLetter or null }
    this.flagged = {}; // { questionIndex: true/false }
    this.timeRemainingSeconds = this.timeLimitMinutes * 60;
    this.timerInterval = null;

    // Attach singleton to window so buttons and external scripts can always invoke it
    window.simulacroEngine = this;

    this.init();
  }

  init() {
    this.bindEvents();
    this.startTimer();
    this.updateUI();
    console.log('[SimulacroEngine] Inicializado con éxito. Total reactivos:', this.totalQuestions);
  }

  startTimer() {
    const timerElement = document.getElementById('examCountdown');
    const timerBox = document.getElementById('timerBox');
    if (!timerElement) return;

    if (this.timerInterval) clearInterval(this.timerInterval);

    this.timerInterval = setInterval(() => {
      this.timeRemainingSeconds--;

      if (this.timeRemainingSeconds <= 0) {
        clearInterval(this.timerInterval);
        this.timeRemainingSeconds = 0;
        timerElement.textContent = "00:00";
        alert("¡El tiempo límite ha expirado! El examen se finalizará y entregará automáticamente.");
        this.submitExam();
        return;
      }

      const minutes = Math.floor(this.timeRemainingSeconds / 60);
      const seconds = this.timeRemainingSeconds % 60;
      timerElement.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

      // Warning styling when under 5 minutes
      if (this.timeRemainingSeconds <= 300 && timerBox) {
        timerBox.classList.add('warning-time');
      }
    }, 1000);
  }

  bindEvents() {
    // Robust document-level event delegation (never fails even if DOM is updated)
    document.addEventListener('click', (e) => {
      // 1. Next Question Button
      const nextBtn = e.target.closest('.next-question-btn, #nextQuestionBtn');
      if (nextBtn) {
        e.preventDefault();
        if (!nextBtn.getAttribute('onclick')) {
          this.nextQuestion();
        }
        return;
      }

      // 2. Previous Question Button
      const prevBtn = e.target.closest('.prev-question-btn, #prevQuestionBtn');
      if (prevBtn) {
        e.preventDefault();
        if (!prevBtn.getAttribute('onclick')) {
          this.prevQuestion();
        }
        return;
      }

      // 3. Navigation Palette Item Click
      const paletteBtn = e.target.closest('.palette-item-btn');
      if (paletteBtn) {
        e.preventDefault();
        const index = parseInt(paletteBtn.getAttribute('data-index'), 10);
        if (!isNaN(index)) {
          this.goToQuestion(index);
        }
        return;
      }

      // 4. Option Choice Card Click
      const optionCard = e.target.closest('.option-choice-card');
      if (optionCard) {
        e.preventDefault();
        const block = optionCard.closest('.question-block');
        if (block) {
          const qIndex = parseInt(block.getAttribute('data-question-index'), 10);
          const letter = optionCard.getAttribute('data-letter');
          const allOptions = block.querySelectorAll('.option-choice-card');
          this.selectOption(qIndex, letter, optionCard, allOptions);
        }
        return;
      }

      // 5. Clear / Leave Blank Button
      const clearBtn = e.target.closest('.clear-selection-btn');
      if (clearBtn) {
        e.preventDefault();
        const block = clearBtn.closest('.question-block');
        if (block) {
          const qIndex = parseInt(block.getAttribute('data-question-index'), 10);
          const allOptions = block.querySelectorAll('.option-choice-card');
          this.clearSelection(qIndex, allOptions);
        }
        return;
      }

      // 6. Flag for Review Button
      const flagBtn = e.target.closest('.flag-review-btn');
      if (flagBtn) {
        e.preventDefault();
        const block = flagBtn.closest('.question-block');
        if (block) {
          const qIndex = parseInt(block.getAttribute('data-question-index'), 10);
          this.toggleFlag(qIndex, flagBtn);
        }
        return;
      }

      // 7. Finish Exam Top Header Button
      const finishBtn = e.target.closest('#finishExamBtn');
      if (finishBtn) {
        e.preventDefault();
        this.openFinishConfirmation();
        return;
      }

      // 8. Confirm Final Submission Inside Modal
      const confirmSubmitBtn = e.target.closest('#confirmSubmitExam');
      if (confirmSubmitBtn) {
        e.preventDefault();
        this.submitExam();
        return;
      }

      // 9. Modal Close Buttons
      const modalCloseBtn = e.target.closest('[data-modal-close]');
      if (modalCloseBtn) {
        e.preventDefault();
        this.closeFinishConfirmation();
        return;
      }
    });
  }

  nextQuestion() {
    if (this.currentQuestionIndex < this.totalQuestions - 1) {
      this.goToQuestion(this.currentQuestionIndex + 1);
    } else {
      this.openFinishConfirmation();
    }
  }

  prevQuestion() {
    if (this.currentQuestionIndex > 0) {
      this.goToQuestion(this.currentQuestionIndex - 1);
    }
  }

  goToQuestion(index) {
    if (index < 0 || index >= this.totalQuestions) return;
    this.currentQuestionIndex = index;
    this.updateUI();
  }

  selectOption(qIndex, letter, selectedElement, allOptions) {
    this.answers[qIndex] = letter;

    if (allOptions) {
      allOptions.forEach(opt => opt.classList.remove('selected'));
    }
    if (selectedElement) {
      selectedElement.classList.add('selected');
    }

    const block = document.querySelector(`.question-block[data-question-index="${qIndex}"]`);
    if (block) {
      const hiddenInput = block.querySelector('.hidden-answer-input');
      if (hiddenInput) hiddenInput.value = letter;
    }

    this.updatePaletteButton(qIndex);
    this.updateStats();
  }

  clearSelection(qIndex, allOptions) {
    delete this.answers[qIndex];
    if (allOptions) {
      allOptions.forEach(opt => opt.classList.remove('selected'));
    }

    const block = document.querySelector(`.question-block[data-question-index="${qIndex}"]`);
    if (block) {
      const hiddenInput = block.querySelector('.hidden-answer-input');
      if (hiddenInput) hiddenInput.value = '';
    }

    this.updatePaletteButton(qIndex);
    this.updateStats();
  }

  toggleFlag(qIndex, flagBtn) {
    this.flagged[qIndex] = !this.flagged[qIndex];

    const block = document.querySelector(`.question-block[data-question-index="${qIndex}"]`);
    if (block) {
      const hiddenRev = block.querySelector('.hidden-revision-input');
      if (hiddenRev) hiddenRev.value = this.flagged[qIndex] ? 'true' : 'false';
    }

    if (flagBtn) {
      if (this.flagged[qIndex]) {
        flagBtn.classList.remove('btn-secondary');
        flagBtn.style.backgroundColor = 'var(--warning-bg)';
        flagBtn.style.borderColor = 'var(--warning-border)';
        flagBtn.style.color = 'var(--warning-text)';
        flagBtn.innerHTML = `
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path>
            <line x1="4" y1="22" x2="4" y2="15"></line>
          </svg>
          Marcada para Revisión
        `;
      } else {
        flagBtn.classList.add('btn-secondary');
        flagBtn.style.backgroundColor = '';
        flagBtn.style.borderColor = '';
        flagBtn.style.color = '';
        flagBtn.innerHTML = `
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path>
            <line x1="4" y1="22" x2="4" y2="15"></line>
          </svg>
          Marcar para Revisión
        `;
      }
    }

    this.updatePaletteButton(qIndex);
    this.updateStats();
  }

  updatePaletteButton(index) {
    const btn = document.querySelector(`.palette-item-btn[data-index="${index}"]`);
    if (!btn) return;

    btn.className = 'palette-item-btn';

    if (index === this.currentQuestionIndex) {
      btn.classList.add('current');
    }

    if (this.flagged[index]) {
      btn.classList.add('flagged');
    } else if (this.answers[index]) {
      btn.classList.add('answered');
    } else {
      btn.classList.add('empty');
    }
  }

  updateUI() {
    // Show current question block, hide others
    const blocks = document.querySelectorAll('.question-block');
    blocks.forEach((block, idx) => {
      if (idx === this.currentQuestionIndex) {
        block.style.display = 'block';
      } else {
        block.style.display = 'none';
      }
    });

    // Update Palette Buttons active state
    for (let i = 0; i < this.totalQuestions; i++) {
      this.updatePaletteButton(i);
    }

    // Update Prev / Next buttons state across all question cards
    document.querySelectorAll('.prev-question-btn').forEach(btn => {
      btn.disabled = this.currentQuestionIndex === 0;
      if (this.currentQuestionIndex === 0) {
        btn.style.opacity = '0.5';
        btn.style.cursor = 'not-allowed';
      } else {
        btn.style.opacity = '1';
        btn.style.cursor = 'pointer';
      }
    });

    document.querySelectorAll('.next-question-btn').forEach(btn => {
      if (this.currentQuestionIndex === this.totalQuestions - 1) {
        btn.innerHTML = `
          Revisar y Entregar
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
        `;
        btn.className = 'btn btn-success next-question-btn';
      } else {
        btn.innerHTML = `
          Siguiente Pregunta
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
        `;
        btn.className = 'btn btn-primary next-question-btn';
      }
    });

    // Update Progress counter
    const currentNumEl = document.getElementById('currentQuestionNumber');
    if (currentNumEl) currentNumEl.textContent = this.currentQuestionIndex + 1;

    this.updateStats();
  }

  updateStats() {
    const answeredCount = Object.keys(this.answers).length;
    const flaggedCount = Object.values(this.flagged).filter(Boolean).length;
    const emptyCount = Math.max(0, this.totalQuestions - answeredCount);

    const answeredEl = document.getElementById('answeredCount');
    const emptyEl = document.getElementById('emptyCount');
    const flaggedEl = document.getElementById('flaggedCount');
    const progressBar = document.getElementById('examProgressBar');

    if (answeredEl) answeredEl.textContent = answeredCount;
    if (emptyEl) emptyEl.textContent = emptyCount;
    if (flaggedEl) flaggedEl.textContent = flaggedCount;

    if (progressBar && this.totalQuestions > 0) {
      const pct = Math.round((answeredCount / this.totalQuestions) * 100);
      progressBar.style.width = `${pct}%`;
    }
  }

  openFinishConfirmation() {
    const answeredCount = Object.keys(this.answers).length;
    const emptyCount = Math.max(0, this.totalQuestions - answeredCount);
    const flaggedCount = Object.values(this.flagged).filter(Boolean).length;

    const summaryEl = document.getElementById('modalFinishSummary');
    if (summaryEl) {
      summaryEl.innerHTML = `
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;text-align:center;margin:12px 0;">
          <div style="background:var(--primary-50);padding:8px;border-radius:6px;border:1px solid var(--primary-200);">
            <strong style="font-size:1.3rem;color:var(--primary-700);font-family:var(--font-mono);">${answeredCount}</strong><br>
            <span style="font-size:0.75rem;color:var(--text-tertiary);">Respondidas</span>
          </div>
          <div style="background:var(--warning-bg);padding:8px;border-radius:6px;border:1px solid var(--warning-border);">
            <strong style="font-size:1.3rem;color:var(--warning-text);font-family:var(--font-mono);">${flaggedCount}</strong><br>
            <span style="font-size:0.75rem;color:var(--warning-text);">En Revisión</span>
          </div>
          <div style="background:var(--bg-subtle);padding:8px;border-radius:6px;border:1px solid var(--border-subtle);">
            <strong style="font-size:1.3rem;color:var(--text-secondary);font-family:var(--font-mono);">${emptyCount}</strong><br>
            <span style="font-size:0.75rem;color:var(--text-tertiary);">En Blanco</span>
          </div>
        </div>
      `;
    }

    if (typeof openModal === 'function') {
      openModal('confirmFinishModal');
    } else {
      const modal = document.getElementById('confirmFinishModal');
      if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
      }
    }
  }

  closeFinishConfirmation() {
    if (typeof closeModal === 'function') {
      closeModal('confirmFinishModal');
    } else {
      const modal = document.getElementById('confirmFinishModal');
      if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
      }
    }
  }

  submitExam() {
    const form = document.getElementById('examForm');
    if (form) {
      form.submit();
    } else {
      console.warn('Formulario examForm no encontrado.');
    }
  }
}

window.SimulacroEngine = SimulacroEngine;
