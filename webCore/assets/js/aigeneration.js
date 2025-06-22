// AI modal
document.addEventListener('DOMContentLoaded', function () {
    const aiGenerateBtn = document.getElementById('aiGenerateCards');
    const aiModal = document.getElementById('aiModal');
    const aiModalContent = document.getElementById('aiModalContent');
    const closeAiModal = document.getElementById('closeAiModal');
    const cancelGeneration = document.getElementById('cancelGeneration');
    const generateCards = document.getElementById('generateCards');
    const cardCountSlider = document.getElementById('cardCountSlider');
    const cardCountValue = document.getElementById('cardCountValue');
    const topicInput = document.getElementById('topicInput');

    let selectedModel = null;
    let availableModels = [];

    // update card count
    cardCountSlider.addEventListener('input', function () {
        cardCountValue.textContent = this.value;
    });

    // open modal
    aiGenerateBtn.addEventListener('click', function () {
        openAiModal();
    });

    // close modal handlers
    closeAiModal.addEventListener('click', closeAiModalHandler);
    cancelGeneration.addEventListener('click', closeAiModalHandler);

    // clost modal when clicking outside
    aiModal.addEventListener('click', function (e) {
        if (e.target === aiModal) {
            closeAiModalHandler();
        }
    });

    // gen cards handler
    generateCards.addEventListener('click', function () {
        handleGenerateCards();
    });

    function openAiModal() {
        aiModal.classList.remove('hidden');
        aiModal.offsetHeight;
        aiModal.classList.remove('opacity-0');
        aiModalContent.classList.remove('scale-95');

        loadModels();
    }

    function closeAiModalHandler() {
        aiModal.classList.add('opacity-0');
        aiModalContent.classList.add('scale-95');

        setTimeout(() => {
            aiModal.classList.add('hidden');

            topicInput.value = '';
            cardCountSlider.value = 5;
            cardCountValue.textContent = '5';
            selectedModel = null;
        }, 300);
    }

    async function loadModels() {
        const modelSelection = document.getElementById('modelSelection');
        const modelsLoading = document.getElementById('modelsLoading');
        const aiProviderName = document.getElementById('aiProviderName');

        try {
            const response = await fetch('/models/getmodels');
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch models');
            }

            // update provider name
            aiProviderName.textContent = data.provider || 'Unknown';

            // hide loading
            modelsLoading.style.display = 'none';

            // populate models
            availableModels = data.data || [];

            if (availableModels.length === 0) {
                modelSelection.innerHTML = `
                            <div class="text-center py-4 text-gray-400">
                                <p>No models available</p>
                            </div>
                        `;
                return;
            }

            // model selection
            const modelsHtml = availableModels.map((model, index) => `
                        <div class="model-option p-3 rounded-xl border border-gray-600/30 hover:border-violet-500/50 cursor-pointer transition-all duration-200 hover:bg-violet-500/5" data-model="${model.id || model.name || model}">
                            <div class="flex items-center gap-3">
                                <div class="w-4 h-4 rounded-full border-2 border-gray-400 model-radio"></div>
                                <div class="flex-1">
                                    <p class="font-medium text-white">${model.name || model.id || model}</p>
                                    ${model.description ? `<p class="text-sm text-gray-400">${model.description}</p>` : ''}
                                </div>
                            </div>
                        </div>
                    `).join('');

            modelSelection.innerHTML = modelsHtml;

            // click handlers
            document.querySelectorAll('.model-option').forEach(option => {
                option.addEventListener('click', function () {
                    document.querySelectorAll('.model-option').forEach(opt => {
                        opt.classList.remove('border-violet-500', 'bg-violet-500/10');
                        opt.querySelector('.model-radio').classList.remove('bg-violet-500', 'border-violet-500');
                    });

                    this.classList.add('border-violet-500', 'bg-violet-500/10');
                    this.querySelector('.model-radio').classList.add('bg-violet-500', 'border-violet-500');

                    selectedModel = this.dataset.model;
                    updateGenerateButton();
                });
            });

            // select first model
            if (availableModels.length > 0) {
                document.querySelector('.model-option').click();
            }

        } catch (error) {
            console.error('Error loading models:', error);
            modelsLoading.innerHTML = `
                        <div class="text-center py-4 text-red-400">
                            <p>Failed to load models</p>
                            <p class="text-sm text-gray-400">${error.message}</p>
                        </div>
                    `;
            aiProviderName.textContent = 'Connection Error';
        }
    }

    function updateGenerateButton() {
        const hasModel = selectedModel !== null;
        const hasTopic = topicInput.value.trim().length > 0;

        generateCards.disabled = !hasModel || !hasTopic;
    }

    // update generate button state when topic changes
    topicInput.addEventListener('input', updateGenerateButton);

    // helper function to add cards to the current deck
    function addGeneratedCardsToDeck(cards) {
        currentDeckIndex = decks.length - 1;

        // see if we have a current deck selected
        if (currentDeckIndex === null) {
            console.error('No deck selected');
            return;
        }

        cards.forEach(card => {
            const formattedCard = {
                front: card.front || card.question || '',
                back: card.back || card.answer || ''
            };

            // add the card to the deck array
            decks[currentDeckIndex].cards.push(formattedCard);
        });

        // re render all cards to update the display
        renderCards();

        // shoq practice button if we have cards
        if (decks[currentDeckIndex].cards.length > 0) {
            const practiceBtn = document.getElementById('practiceWithCards');
            if (practiceBtn) {
                practiceBtn.classList.remove('hidden');
            }
        }

        // scroll to the last added card
        setTimeout(() => {
            const cardsList = document.getElementById('cardsList');
            if (cardsList && cardsList.lastElementChild) {
                cardsList.lastElementChild.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        }, 200);
    }


    async function handleGenerateCards() {
        if (!selectedModel || !topicInput.value.trim()) {
            return;
        }

        const topic = topicInput.value.trim();
        const cardCount = parseInt(cardCountSlider.value);

        // show loading state
        generateCards.disabled = true;
        generateCards.innerHTML = `
                    <span class="flex items-center justify-center gap-2">
                        <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        Generating...
                    </span>
                `;

        try {
            if (window.notyf) {
                window.notyf.success('AI generation started. Please be patient, this may take some time depending on model type and hardware/software.');
            }

            const response = await fetch("/models/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    model: selectedModel,
                    topic: topic,
                    cardCount: cardCount
                })
            });

            const data = await response.json();

            if (!response.ok) {
                const errorMessage = data?.message || "Generation failed, please try again later.";
                if (window.notyf) {
                    window.notyf.error(errorMessage);
                }
                return;
            }

            // check if response has expected structure
            if (data.status && data.message && data.message.cards && Array.isArray(data.message.cards)) {
                const generatedCards = data.message.cards;

                // add the generated cards to the current deck
                addGeneratedCardsToDeck(generatedCards);

                // close modal
                closeAiModalHandler();

                if (window.notyf) {
                    window.notyf.success(`Successfully generated ${generatedCards.length} cards for "${topic}"`);
                }

                const deckNameInput = document.getElementById('deckNameInput');
                if (!deckNameInput.value.trim()) {
                    deckNameInput.value = topic;
                }

            } else {
                console.error('Unexpected response format:', data);
                if (window.notyf) {
                    window.notyf.error('Received unexpected response format from server');
                }
            }

        } catch (error) {
            console.error('Error generating cards:', error);
            if (window.notyf) {
                window.notyf.error('Failed to generate cards. Please check your connection and try again.');
            }
        } finally {
            // reset button
            generateCards.disabled = false;
            generateCards.innerHTML = `
                        <span class="flex items-center justify-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                            </svg>
                            Generate Cards
                        </span>
                    `;
        }
    }
});