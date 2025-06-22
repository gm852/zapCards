// notifications
const notyf = new Notyf({
    duration: 5000,
    position: { x: 'right', y: 'top' },
    dismissible: true,
    ripple: true,
    types: [
        {
            type: 'success',
            background: 'linear-gradient(135deg, #10b981, #06b6d4)',
        },
        {
            type: 'error',
            background: 'linear-gradient(135deg, #ef4444, #dc2626)',
        }
    ]
});

let decks = [];
let currentDeckIndex = null;

// Cached elements
const deckListEl = document.getElementById('deckList');
const newDeckBtn = document.getElementById('newDeckBtn');
const deckEditor = document.getElementById('deckEditor');
const deckTitleEl = document.getElementById('deckTitle');
const deckNameInput = document.getElementById('deckNameInput');
const cardsList = document.getElementById('cardsList');
const addCardBtn = document.getElementById('addCardBtn');
const saveDeckBtn = document.getElementById('saveDeckBtn');
const practiceBtn = document.getElementById('practiceWithCards');
const deckCountEl = document.getElementById('deckCount');
const cardCountEl = document.getElementById('cardCount');
const loadingState = document.getElementById('loadingState');

// deck name input handling
deckNameInput.addEventListener('input', (e) => {
    if (currentDeckIndex !== null) {
        decks[currentDeckIndex].name = e.target.value;
        updateDeckTitle();
        renderDeckList();
    }
});


function updateDeckTitle() {
    if (currentDeckIndex !== null) {
        const deckName = decks[currentDeckIndex].name || 'Untitled Deck';
        deckTitleEl.innerHTML = `Editing: <span class="text-violet-400">${deckName}</span>`;
    }
}

// counters
function updateCounters() {
    deckCountEl.textContent = `${decks.length} deck${decks.length !== 1 ? 's' : ''}`;
    if (currentDeckIndex !== null) {
        const cardCount = decks[currentDeckIndex].cards.length;
        cardCountEl.textContent = `${cardCount} card${cardCount !== 1 ? 's' : ''}`;
    }
}

// deck list rendering
function renderDeckList() {
    deckListEl.innerHTML = '';

    if (decks.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'text-center py-8 text-gray-400';
        emptyState.innerHTML = `
          <svg class="w-12 h-12 mx-auto mb-3 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
          </svg>
          <p>No decks yet</p>
          <p class="text-sm mt-1">Create your first deck to get started</p>
        `;
        deckListEl.appendChild(emptyState);
        updateCounters();
        return;
    }

    decks.forEach((deck, i) => {
        const li = document.createElement('li');
        li.className = `deck-item p-4 rounded-xl cursor-pointer transition-all duration-300 ${i === currentDeckIndex ? 'active' : ''
            }`;

        li.innerHTML = `
          <div class="flex items-center justify-between">
            <div class="flex-1 min-w-0">
              <h4 class="font-medium text-white truncate">${deck.name || 'Untitled Deck'}</h4>
              <p class="text-sm text-gray-400 mt-1">${deck.cards.length} card${deck.cards.length !== 1 ? 's' : ''}</p>
            </div>
            <div class="flex items-center gap-2 ml-3">
              <button class="delete-btn p-2 rounded-lg text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-all" title="Delete Deck">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
              </button>
            </div>
          </div>
        `;

        const deleteBtn = li.querySelector('.delete-btn');
        deleteBtn.onclick = async (e) => {
            e.stopPropagation();
            if (confirm(`Delete deck "${deck.name || 'Untitled Deck'}"?`)) {
                await deleteDeck(deck, i);
            }
        };

        li.onclick = () => {
            currentDeckIndex = i;
            renderDeckList();
            openDeckEditor(decks[i]);
        };

        deckListEl.appendChild(li);
    });

    updateCounters();
}

// card element
function createCardElement(card, idx) {
    const container = document.createElement('div');
    container.className = 'card-container';

    container.innerHTML = `
        <div class="flashcard">
          <div class="flip-indicator">Click edges to flip</div>
          <div class="flashcard-inner">
            <div class="front">
              <textarea 
                class="card-textarea front-textarea" 
                placeholder="Enter your question here..."
                rows="6"
              >${card.front}</textarea>
            </div>
            <div class="back">
              <textarea 
                class="card-textarea back-textarea" 
                placeholder="Enter your answer here..."
                rows="6"
              >${card.back}</textarea>
            </div>
          </div>
        </div>
        <div class="flex justify-between items-center mt-4">
          <div class="text-sm text-gray-400">Card ${idx + 1}</div>
          <button class="remove-btn btn-danger rounded-lg py-2 px-4 text-sm font-medium">
            <span class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
              Remove Card
            </span>
          </button>
        </div>
      `;

    const flashcard = container.querySelector('.flashcard');
    const frontTextarea = container.querySelector('.front-textarea');
    const backTextarea = container.querySelector('.back-textarea');
    const removeBtn = container.querySelector('.remove-btn');

    // flip logic
    flashcard.addEventListener('click', (e) => {
        if (e.target.tagName === 'TEXTAREA') return;

        const rect = flashcard.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const clickZone = 50;

        if (clickX < clickZone || clickX > rect.width - clickZone) {
            flashcard.classList.toggle('flip');
        }
    });

    let frontTimeout, backTimeout;

    frontTextarea.oninput = (e) => {
        clearTimeout(frontTimeout);
        frontTimeout = setTimeout(() => {
            decks[currentDeckIndex].cards[idx].front = e.target.value;
            updateCounters();
        }, 300);
    };

    backTextarea.oninput = (e) => {
        clearTimeout(backTimeout);
        backTimeout = setTimeout(() => {
            decks[currentDeckIndex].cards[idx].back = e.target.value;
            updateCounters();
        }, 300);
    };

    removeBtn.onclick = () => {
        if (confirm('Remove this card?')) {
            decks[currentDeckIndex].cards.splice(idx, 1);
            renderCards();
            updateCounters();
            notyf.success('Card removed successfully');
        }
    };

    return container;
}

// card rendering
function renderCards(addedIndex = null) {
    cardsList.innerHTML = '';

    if (currentDeckIndex === null) return;

    const cards = decks[currentDeckIndex].cards || [];

    if (cards.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'text-center py-12 text-gray-400';
        emptyState.innerHTML = `
          <svg class="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
          </svg>
          <p class="text-lg font-medium mb-2">No cards yet</p>
          <p>Add your first card to start building this deck</p>
        `;
        cardsList.appendChild(emptyState);
        return;
    }

    cards.forEach((card, idx) => {
        const cardEl = createCardElement(card, idx);

        if (idx === addedIndex) {
            cardEl.classList.add('card-enter');
        }

        cardsList.appendChild(cardEl);
    });

    updateCounters();
}

// deck editor
function openDeckEditor(deck) {
    deckEditor.classList.remove('hidden');
    deckEditor.classList.add('flex');
    deckNameInput.value = deck.name || '';
    updateDeckTitle();
    renderCards();
    practiceBtn.classList.toggle('hidden', !deck.cards.length);

    // scroll to top
    setTimeout(() => {
        deckEditor.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}


newDeckBtn.onclick = () => {
    decks.push({ name: '', cards: [], deckID: null });
    currentDeckIndex = decks.length - 1;
    renderDeckList();
    openDeckEditor(decks[currentDeckIndex]);

    setTimeout(() => deckNameInput.focus(), 300);
};

async function addNewCard() {
    if (currentDeckIndex === null) return;

    decks[currentDeckIndex].cards.push({ front: '', back: '' });
    const newCardIndex = decks[currentDeckIndex].cards.length - 1;

    renderCards(newCardIndex);

    // show practice button if this is the first card
    if (decks[currentDeckIndex].cards.length === 1) {
        const practiceBtn = document.getElementById('practiceWithCards');
        if (practiceBtn) {
            practiceBtn.classList.remove('hidden');
        }
    }

    // scroll to new card
    setTimeout(() => {
        const cardsList = document.getElementById('cardsList');
        const newCard = cardsList ? cardsList.lastElementChild : null;
        if (newCard) {
            newCard.scrollIntoView({ behavior: 'smooth', block: 'center' });

            const frontTextarea = newCard.querySelector('.front-textarea');
            if (frontTextarea) frontTextarea.focus();
        }
    }, 200);
}

// save 
async function saveDeck(isSilent = false) {
    if (currentDeckIndex === null) {
        if (!isSilent) notyf.error('No deck selected');
        return;
    }


    const deck = decks[currentDeckIndex];
    deck.name = deckNameInput.value.trim();

    if (!deck.name) {
        if (!isSilent) {
            notyf.error('Please enter a deck name');
            deckNameInput.focus();
        }
        return;
    }

    if (deck.cards.length === 0) {
        if (!isSilent) notyf.error('Add at least one card to save the deck');
        return;
    }

    const emptyCards = [];
    for (let i = 0; i < deck.cards.length; i++) {
        if (!deck.cards[i].front.trim() || !deck.cards[i].back.trim()) {
            emptyCards.push(i + 1);
        }
    }

    if (emptyCards.length > 0) {
        if (!isSilent) notyf.error(`Please fill in both sides of card${emptyCards.length > 1 ? 's' : ''}: ${emptyCards.join(', ')}`);
        return;
    }

    // show loading state
    if (!isSilent) {
        saveDeckBtn.innerHTML = `
          <span class="flex items-center gap-2">
            <svg class="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
            </svg>
            Saving...
          </span>
        `;
        saveDeckBtn.disabled = true;
    }

    try {

        const response = await fetch('/api/deck/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(deck),
        });

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();

        if (data.status) {
            if (!isSilent) notyf.success(`"${deck.name}" saved successfully!`);

            // prevents creating duplicate decks
            if (data.deckID && !deck.deckID) {
                decks[currentDeckIndex].deckID = data.deckID;
                console.log(`Assigned new deckID: ${data.deckID} to deck: ${deck.name}`);
            }

            // show updated info
            renderDeckList();
        } else {
            if (!isSilent) notyf.error(data.message || 'Failed to save deck');
        }
    } catch (e) {
        if (!isSilent) notyf.error('Error saving deck: ' + e.message);
        console.error('Save error:', e);
    } finally {
        // reset button
        if (!isSilent) {
            saveDeckBtn.innerHTML = `
            <span class="flex items-center gap-2">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3-3m0 0l-3 3m3-3v12"></path>
              </svg>
              Save Deck
            </span>
          `;
            saveDeckBtn.disabled = false;
        }
    }
}


saveDeckBtn.onclick = () => saveDeck(false);
addCardBtn.onclick = () => addNewCard();

// delete deck
async function deleteDeck(deck, deckIndex) {
    const deckItem = deckListEl.children[deckIndex];
    if (deckItem) {
        deckItem.style.opacity = '0.5';
        deckItem.style.pointerEvents = 'none';
    }

    if (deck.deckID) {
        try {
            const response = await fetch('/api/decks/delete', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ deckID: deck.deckID }),
            });

            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

            const data = await response.json();
            if (!data.status) {
                notyf.error(data.message || 'Failed to delete deck from server');
                // reset
                if (deckItem) {
                    deckItem.style.opacity = '1';
                    deckItem.style.pointerEvents = 'auto';
                }
                return;
            }
        } catch (e) {
            notyf.error('Error deleting deck: ' + e.message);
            // reset
            if (deckItem) {
                deckItem.style.opacity = '1';
                deckItem.style.pointerEvents = 'auto';
            }
            return;
        }
    }

    decks.splice(deckIndex, 1);

    if (currentDeckIndex === deckIndex) {
        currentDeckIndex = null;
        deckEditor.classList.add('hidden');
        deckEditor.classList.remove('flex');
        deckTitleEl.textContent = 'Select or create a deck';
    } else if (currentDeckIndex > deckIndex) {
        currentDeckIndex--;
    }

    renderDeckList();
    notyf.success(`"${deck.name || 'Untitled Deck'}" deleted successfully`);
}

async function fetchUserDecks() {
    try {
        loadingState.classList.remove('hidden');

        const response = await fetch('/api/decks/get');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const data = await response.json();
        console.log('API Response:', data);

        let cardsArray = [];

        if (data.status && Array.isArray(data.decks)) {
            cardsArray = data.decks;
        } else {
            console.warn('Unexpected API response format:', data);
            cardsArray = [];
        }

        // proccess array
        decks = cardsArray.map(deck => ({
            name: deck.name || 'Untitled Deck',
            cards: Array.isArray(deck.cards) ? deck.cards.map(card => ({
                front: card.front || '',
                back: card.back || ''
            })) : [],
            deckID: deck.deckID || null
        }));


        renderDeckList();

        if (decks.length > 0) {
            notyf.success(`Welcome back! Loaded ${decks.length} deck${decks.length !== 1 ? 's' : ''}`);
        } else {
            setTimeout(() => {
                notyf.success('Welcome to ZapCards! Create your first deck to get started.');
            }, 1000);
        }

    } catch (err) {
        console.error('Fetch error:', err);
        notyf.error("Unable to load your decks. Please check your connection and try again.");

        // empty state on issue
        decks = [];
        renderDeckList();
    } finally {
        loadingState.classList.add('hidden');
    }
}


// shortcuts
document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        if (currentDeckIndex !== null) {
            saveDeckBtn.click();
        }
    }

    if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        newDeckBtn.click();
    }

    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        if (currentDeckIndex !== null) {
            addNewCard();
        }
    }
});

// autosave
setInterval(() => {
    if (currentDeckIndex !== null && decks[currentDeckIndex].name.trim() && decks[currentDeckIndex].cards.length > 0) {
        // if all cards are filled
        const allCardsFilled = decks[currentDeckIndex].cards.every(card =>
            card.front.trim() && card.back.trim()
        );

        if (allCardsFilled && !saveDeckBtn.disabled) {
            // save silently
            saveDeck(true);
        }
    }
}, 30000); // autosave every 30 seconds

// initialization
window.onload = async () => {
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease';
        document.body.style.opacity = '1';
    }, 100);

    await fetchUserDecks();

    if (decks.length === 0) {
        setTimeout(() => {
            newDeckBtn.classList.add('pulse-animation');
            setTimeout(() => {
                newDeckBtn.classList.remove('pulse-animation');
            }, 3000);
        }, 2000);
    }
};

// resize handler
window.addEventListener('resize', () => {
    if (window.innerWidth < 1024 && deckEditor.classList.contains('flex')) {
        // On mobile, ensure deck editor is visible
        setTimeout(() => {
            deckEditor.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 100);
    }
});

// warn about unsaved changes
window.addEventListener('beforeunload', (e) => {
    if (currentDeckIndex !== null) {
        const deck = decks[currentDeckIndex];
        if (deck.name.trim() && deck.cards.some(card => card.front.trim() || card.back.trim())) {
            e.preventDefault();
        }
    }
});





// PRACTICE MODE JS
let currentDeck = null;
let currentCardIndex = 0;
let isFlipped = false;

// event listeners
document.getElementById('practiceWithCards').addEventListener('click', function () {
    console.log(currentDeckIndex, decks[currentDeckIndex].cards.length)
    console.log(decks)
    if (currentDeckIndex === null || decks[currentDeckIndex].cards.length === 0) {
        notyf.error('No cards to practice with');
        return;
    } else {
        // Set the currentDeck to the selected deck from the decks array
        currentDeck = decks[currentDeckIndex];
        enterPracticeMode();
    }
});
document.getElementById('exitPractice').addEventListener('click', exitPracticeMode);
document.getElementById('flipCard').addEventListener('click', flipCard);
document.getElementById('flashcard').addEventListener('click', flipCard);
document.getElementById('nextCard').addEventListener('click', nextCard);
document.getElementById('prevCard').addEventListener('click', prevCard);
document.getElementById('editCurrentCard').addEventListener('click', exitPracticeMode);


// shortcuts
document.addEventListener('keydown', function (e) {
    if (document.getElementById('practiceMode').classList.contains('hidden')) return;

    switch (e.key) {
        case 'ArrowLeft':
            e.preventDefault();
            prevCard();
            break;
        case 'ArrowRight':
            e.preventDefault();
            nextCard();
            break;
        case ' ':
        case 'Enter':
            e.preventDefault();
            flipCard();
            break;
        case 'Escape':
            e.preventDefault();
            exitPracticeMode();
            break;
    }
});

function enterPracticeMode() {
    currentCardIndex = 0;
    isFlipped = false;
    document.getElementById('practiceMode').classList.remove('hidden');
    document.getElementById('practiceTitle').textContent = `Practice: ${currentDeck.name}`;
    updatePracticeCard();
    updateNavigationButtons();
}

function exitPracticeMode() {
    document.getElementById('practiceMode').classList.add('hidden');
    isFlipped = false;
    document.getElementById('cardInner').classList.remove('flipped');
}

async function flipCard() {
    isFlipped = !isFlipped;
    const cardInner = document.getElementById('cardInner');
    if (isFlipped) {
        cardInner.classList.add('flipped');
    } else {
        cardInner.classList.remove('flipped');
    }
}

async function nextCard() {
    if (currentCardIndex < currentDeck.cards.length - 1) {
        isFlipped = false;
        document.getElementById('cardInner').classList.remove('flipped');

        await new Promise((resolve) => setTimeout(resolve, 200));
        currentCardIndex++;

        updatePracticeCard();
        updateNavigationButtons();
    }
}

async function prevCard() {
    if (currentCardIndex > 0) {
        currentCardIndex--;
        isFlipped = false;
        document.getElementById('cardInner').classList.remove('flipped');
        updatePracticeCard();
        updateNavigationButtons();
    }
}

async function updatePracticeCard() {
    if (!currentDeck || !currentDeck.cards || currentDeck.cards.length === 0) return;

    const card = currentDeck.cards[currentCardIndex];

    document.getElementById('questionText').textContent = card.front || 'No question';
    document.getElementById('answerText').textContent = card.back || 'No answer';
    document.getElementById('currentCardNumber').textContent = currentCardIndex + 1;
    document.getElementById('totalCards').textContent = currentDeck.cards.length;
}

function updateNavigationButtons() {
    const prevBtn = document.getElementById('prevCard');
    const nextBtn = document.getElementById('nextCard');

    prevBtn.disabled = currentCardIndex === 0;
    nextBtn.disabled = currentCardIndex === currentDeck.cards.length - 1;
}
