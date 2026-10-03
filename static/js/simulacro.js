/* ==========================================================================
   SIMULADOR DE CUESTIONARIOS SABER TyT - EXAM ENGINE JS
   ========================================================================== */

class SimulacroEngine {
  constructor(config) {
    this.totalQuestions = config.totalQuestions || 5;
    this.timeLimitMinutes = config.timeLimitMinutes || 45;
    this.currentQuestionIndex = 0;
    this.answers = {}; // { questionIndex: selectedOptionLetter or null }
    this.flagged = {}; // { questionIndex: true/false }
    this.timeRemainingSeconds = this.timeLimitMinutes * 60;
    this.timerInterval = null;

    this.init();
  }

  init() {
    this.bindEvents();
    this.startTimer();
    this.updateUI();
  }

  startTimer() {
    const timerElement = document.getElementById('examCountdown');
    const timerBox = document.getElementById('timerBox');
    if (!timerElement) return;

    this.timerInterval = setInterval(() => {
      this.timeRemainingSeconds--;

      if (this.timeRemainingSeconds <= 0) {
        clearInterval(this.timerInterval);
        this.timeRemainingSeconds = 0;
        timerElement.textContent = "00:00";
        alert("¡El tiempo límite ha expirado! El examen se finalizará automáticamente.");
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
    // Navigation Palette Buttons
    document.querySelectorAll('.palette-item-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const index = parseInt(btn.getAttribute('data-index'), 10);
        this.goToQuestion(index);
      });
    });

    // Previous / Next Buttons
    const prevBtn = document.getElementById('prevQuestionBtn');
    const nextBtn = document.getElementById('nextQuestionBtn');

    if (prevBtn) {
      prevBtn.addEventListener('click', () => {
        if (this.currentQuestionIndex > 0) {
          this.goToQuestion(this.currentQuestionIndex - 1);
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener('click', () => {
        if (this.currentQuestionIndex < this.totalQuestions - 1) {
          this.goToQuestion(this.currentQuestionIndex + 1);
        } else {
          this.openFinishConfirmation();
        }
      });
    }

    // Option Selection
    document.querySelectorAll('.question-block').forEach(block => {
      const qIndex = parseInt(block.getAttribute('data-question-index'), 10);
      const options = block.querySelectorAll('.option-choice-card');

      options.forEach(opt => {
        opt.addEventListener('click', () => {
          const letter = opt.getAttribute('data-letter');
          this.selectOption(qIndex, letter, opt, options);
        });
      });

      // Clear button
      const clearBtn = block.querySelector('.clear-selection-btn');
      if (clearBtn) {
        clearBtn.addEventListener('click', () => {
          this.clearSelection(qIndex, options);
        });
      }

      // Flag for review button
      const flagBtn = block.querySelector('.flag-review-btn');
      if (flagBtn) {
        flagBtn.addEventListener('click', () => {
          this.toggleFlag(qIndex, flagBtn);
        });
      }
    });

    // Finish Exam Button
    const finishBtn = document.getElementById('finishExamBtn');
    if (finishBtn) {
      finishBtn.addEventListener('click', () => {
        this.openFinishConfirmation();
      });
    }

    // Confirm submission
    const confirmSubmitBtn = document.getElementById('confirmSubmitExam');
    if (confirmSubmitBtn) {
      confirmSubmitBtn.addEventListener('click', () => {
        this.submitExam();
      });
    }
  }

  goToQuestion(index) {
    if (index < 0 || index >= this.totalQuestions) return;
    this.currentQuestionIndex = index;
    this.updateUI();
  }

  selectOption(qIndex, letter, selectedElement, allOptions) {
    this.answers[qIndex] = letter;

    allOptions.forEach(opt => opt.classList.remove('selected'));
    selectedElement.classList.add('selected');

    this.updatePaletteButton(qIndex);
    this.updateStats();
  }

  clearSelection(qIndex, allOptions) {
    delete this.answers[qIndex];
    allOptions.forEach(opt => opt.classList.remove('selected'));
    this.updatePaletteButton(qIndex);
    this.updateStats();
  }

  toggleFlag(qIndex, flagBtn) {
    this.flagged[qIndex] = !this.flagged[qIndex];

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
    document.querySelectorAll('.question-block').forEach((block, idx) => {
      block.style.display = idx === this.currentQuestionIndex ? 'block' : 'none';
    });

    // Update Palette Buttons active state
    for (let i = 0; i < this.totalQuestions; i++) {
      this.updatePaletteButton(i);
    }

    // Update Prev / Next buttons state
    const prevBtn = document.getElementById('prevQuestionBtn');
    const nextBtn = document.getElementById('nextQuestionBtn');
    if (prevBtn) prevBtn.disabled = this.currentQuestionIndex === 0;
    if (nextBtn) {
      if (this.currentQuestionIndex === this.totalQuestions - 1) {
        nextBtn.innerHTML = `
          Revisar y Entregar
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
        `;
      } else {
        nextBtn.innerHTML = `
          Siguiente Pregunta
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"></polyline></svg>
        `;
      }
    }

    // Update Progress counter
    const currentNumEl = document.getElementById('currentQuestionNumber');
    if (currentNumEl) currentNumEl.textContent = this.currentQuestionIndex + 1;

    this.updateStats();
  }

  updateStats() {
    const answeredCount = Object.keys(this.answers).length;
    const flaggedCount = Object.values(this.flagged).filter(Boolean).length;
    const emptyCount = this.totalQuestions - answeredCount;

    const answeredEl = document.getElementById('answeredCount');
    const emptyEl = document.getElementById('emptyCount');
    const flaggedEl = document.getElementById('flaggedCount');
    const progressBar = document.getElementById('examProgressBar');

    if (answeredEl) answeredEl.textContent = answeredCount;
    if (emptyEl) emptyEl.textContent = emptyCount;
    if (flaggedEl) flaggedEl.textContent = flaggedCount;

    if (progressBar) {
      const pct = Math.round((answeredCount / this.totalQuestions) * 100);
      progressBar.style.width = `${pct}%`;
    }
  }

  openFinishConfirmation() {
    const answeredCount = Object.keys(this.answers).length;
    const emptyCount = this.totalQuestions - answeredCount;
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
    }
  }

  submitExam() {
    const form = document.getElementById('examForm');
    if (form) {
      form.submit();
    } else {
      const resultUrl = '/estudiante/simulacro/1/resultado/';
      window.location.href = resultUrl;
    }
  }
}

window.SimulacroEngine = SimulacroEngine;
