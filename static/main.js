    document.querySelectorAll('[data-upload]').forEach((dropZone) => {
        const fileInput = dropZone.querySelector('input[type=file]');
        const uploadRow = dropZone.querySelector('.upload-row');
        const uploadAdd = dropZone.querySelector('.upload-add');
        const fileName = dropZone.querySelector('[data-file-name]');
        const defaultPreview = dropZone.querySelector('[data-preview]')?.closest('.upload-preview');

        let accumulatedFiles = [];

        function renderPreviews() {
            uploadRow.querySelectorAll('.dynamic-preview').forEach((el) => el.remove());

            const dt = new DataTransfer();
            accumulatedFiles.forEach((f) => dt.items.add(f));
            fileInput.files = dt.files;

            if (!accumulatedFiles.length) {
                fileName.textContent = '선택한 파일이 없습니다.';
                if (defaultPreview) defaultPreview.style.display = '';
                return;
            }

            fileName.textContent = `${accumulatedFiles.length}개의 사진 선택됨 (${accumulatedFiles.map((f) => f.name).join(', ')})`;
            if (defaultPreview) defaultPreview.style.display = 'none';

            accumulatedFiles.forEach((file, index) => {
                const div = document.createElement('div');
                div.className = 'upload-preview dynamic-preview';

                const img = document.createElement('img');
                img.src = URL.createObjectURL(file);
                div.appendChild(img);

                const removeBtn = document.createElement('button');
                removeBtn.type = 'button';
                removeBtn.className = 'remove-btn';
                removeBtn.textContent = '✕';
                removeBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    accumulatedFiles.splice(index, 1);
                    renderPreviews();
                });
                div.appendChild(removeBtn);

                uploadRow.insertBefore(div, uploadAdd);
            });
        }

        fileInput.addEventListener('change', () => {
            const newFiles = Array.from(fileInput.files || []);
            accumulatedFiles = accumulatedFiles.concat(newFiles);
            fileInput.value = '';
            renderPreviews();
        });

        dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            if (e.dataTransfer.files.length) {
                accumulatedFiles = accumulatedFiles.concat(Array.from(e.dataTransfer.files));
                renderPreviews();
            }
        });
    });
    if (document.getElementById("option-form")) {
        const optionForm = document.getElementById('option-form');
        const quantity = document.getElementById('quantity');
        const total = document.getElementById('option-total');
        const price = Number(optionForm.dataset.price);

        function setQuantity(value) {
            quantity.value = Math.min(Math.max(value || 1, 1), 99);
            total.textContent = (price * Number(quantity.value)).toLocaleString('ko-KR');
        }

        optionForm.querySelectorAll('[data-step]').forEach((button) => {
            button.addEventListener('click', () => {
                setQuantity(Number(quantity.value) + Number(button.dataset.step));
            });
        });
        quantity.addEventListener('change', () => setQuantity(Number(quantity.value)));
        // 첫 제출 버튼이 구매하기이므로, 입력 중 Enter로 참여가 기록되지 않게 막는다.
        optionForm.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && event.target.tagName === 'INPUT') {
                event.preventDefault();
                if (event.target === quantity) setQuantity(Number(quantity.value));
            }
        });
    }

    document.querySelectorAll('[data-dismiss]').forEach((button) => {
        button.addEventListener('click', () => button.closest('.notice').remove());
    });

    document.querySelectorAll('[data-go-back]').forEach((button) => {
        button.addEventListener('click', () => {
            if (history.length > 1) history.back();
            else location.href = '/';
        });
    });

    document.querySelectorAll('[data-toggle-password]').forEach((button) => {
        const input = document.getElementById(button.dataset.togglePassword);
        const showLabel = button.getAttribute('aria-label');
        button.addEventListener('click', () => {
            const show = input.type === 'password';
            input.type = show ? 'text' : 'password';
            button.setAttribute('aria-label', show ? showLabel.replace('보기', '숨기기') : showLabel);
        });
    });

    document.querySelectorAll('[data-help]').forEach((button) => {
        button.addEventListener('click', () => {
            document.getElementById('help-text').textContent = button.dataset.help;
            document.getElementById('help-dialog').showModal();
        });
    });

    document.querySelectorAll('[data-check-id]').forEach((button) => {
        const username = document.getElementById('username');
        const message = document.getElementById('id-check-message');
        username.addEventListener('input', () => { message.textContent = ''; });
        button.addEventListener('click', async () => {
            const value = username.value;
            try {
                const response = await fetch(`${button.dataset.checkId}?username=${encodeURIComponent(value)}`);
                const result = await response.json();
                if (username.value !== value) return;
                message.textContent = `${result.available ? '✓ ' : ''}${result.message}`;
                message.classList.toggle('ok', result.available);
            } catch {
                message.classList.remove('ok');
                message.textContent = '아이디를 확인하지 못했어요. 다시 시도해 주세요.';
            }
        });
    });

    // 임시 저장은 이 브라우저에만 남으며 사진은 저장하지 않는다.
    function draftFields(form) {
        return [...form.elements].filter((field) => field.name && !field.readOnly && !['file', 'hidden', 'submit', 'button'].includes(field.type));
    }

    function saveDraft(form) {
        const values = {};
        draftFields(form).forEach((field) => {
            if (field.type === 'checkbox') values[field.name] = field.checked;
            else if (field.type !== 'radio' || field.checked) values[field.name] = field.value;
        });
        try {
            localStorage.setItem(`draft:${form.dataset.draft}`, JSON.stringify(values));
            return true;
        } catch {
            return false;
        }
    }

    document.querySelectorAll('[data-draft]').forEach((form) => {
        const status = form.querySelector('[data-draft-status]');
        let saved = null;
        try {
            saved = JSON.parse(localStorage.getItem(`draft:${form.dataset.draft}`));
        } catch {
            saved = null;
        }
        if (saved) {
            draftFields(form).forEach((field) => {
                if (!(field.name in saved)) return;
                if (field.type === 'radio') field.checked = field.value === saved[field.name];
                else if (field.type === 'checkbox') field.checked = saved[field.name] === true;
                else field.value = saved[field.name];
            });
            status.textContent = '임시 저장한 내용을 불러왔습니다. 사진은 다시 선택해 주세요.';
        }
        form.querySelector('[data-save-draft]').addEventListener('click', () => {
            status.textContent = saveDraft(form)
                ? '임시 저장했습니다. 사진은 저장되지 않습니다.'
                : '이 브라우저에서는 임시 저장을 사용할 수 없습니다.';
        });
        form.addEventListener('submit', () => {
            try {
                localStorage.removeItem(`draft:${form.dataset.draft}`);
            } catch {
                // 저장소를 쓸 수 없으면 지울 내용도 없다.
            }
        });
    });

    // 상품 등록의 사이즈·색상 입력. 숨긴 textarea에 한 줄에 하나씩 담아 보내므로 임시 저장도 그대로 된다.
    const COLOR_HINTS = { 블랙: '#17212c', 화이트: '#ffffff', 아이보리: '#f4f0e4', 그레이: '#9a9ea3', 차콜: '#3a3d40', 네이비: '#1f2a44', 블루: '#2b5ea7', 그린: '#2f6b4f', 레드: '#b3261e', 핑크: '#f2b8c6', 베이지: '#d9c9a8', 브라운: '#6b4a32' };
    const optionSection = document.querySelector('[data-option-section]');
    if (optionSection) {
        const form = optionSection.closest('form');
        const category = form.querySelector('#category');
        const groups = [...optionSection.querySelectorAll('[data-option-group]')].map((group) => {
            const isColor = group.dataset.optionGroup === 'color';
            const store = group.querySelector('[data-option-store]');
            const list = group.querySelector('[data-option-tags]');
            const add = group.querySelector('[data-option-add]');
            const toggle = group.querySelector('[data-option-toggle]');
            const body = group.querySelector('[data-option-body]');
            const label = isColor ? '색상' : '사이즈';
            const items = store.value.split('\n').map((line) => line.trim()).filter(Boolean).map((line) => {
                const cut = line.lastIndexOf('|');
                return isColor && cut > 0 ? { name: line.slice(0, cut), hex: line.slice(cut + 1) } : { name: line, hex: '' };
            });

            function save() {
                store.value = items.map((item) => (isColor ? `${item.name}|${item.hex}` : item.name)).join('\n');
            }

            function render() {
                save();
                list.replaceChildren(...items.map((item) => {
                    const tag = document.createElement('span');
                    tag.className = 'option-tag';
                    if (isColor) {
                        const swatch = document.createElement('input');
                        swatch.type = 'color';
                        swatch.className = 'option-swatch';
                        swatch.value = /^#[0-9a-f]{6}$/i.test(item.hex) ? item.hex : '#cccccc';
                        swatch.setAttribute('aria-label', `${item.name} 실제 색 지정`);
                        swatch.addEventListener('input', () => { item.hex = swatch.value; save(); });
                        tag.append(swatch);
                    }
                    tag.append(item.name);
                    const remove = document.createElement('button');
                    remove.type = 'button';
                    remove.textContent = '✕';
                    remove.setAttribute('aria-label', `${item.name} 삭제`);
                    remove.addEventListener('click', () => {
                        items.splice(items.indexOf(item), 1);
                        render();
                        add.focus();
                    });
                    tag.append(remove);
                    return tag;
                }));
            }

            function addNames(names) {
                names.map((name) => name.replace(/\|/g, '').trim()).filter(Boolean).forEach((name) => {
                    if (items.length < 20 && !items.some((item) => item.name === name)) {
                        items.push({ name, hex: COLOR_HINTS[name] || '' });
                    }
                });
                add.setCustomValidity('');
                render();
            }

            add.addEventListener('keydown', (event) => {
                if (event.key !== 'Enter' || event.isComposing) return;
                event.preventDefault();
                addNames(add.value.split(','));
                add.value = '';
            });
            add.addEventListener('input', () => add.setCustomValidity(''));
            group.querySelectorAll('[data-preset]').forEach((button) => {
                button.addEventListener('click', () => addNames(button.dataset.preset.split(',')));
            });
            toggle.addEventListener('change', () => { body.hidden = !toggle.checked; });
            body.hidden = !toggle.checked;
            render();

            return {
                // 입력만 하고 Enter를 누르지 않은 값도 제출할 때 함께 담는다.
                commit() {
                    if (add.value.trim()) addNames(add.value.split(','));
                    add.value = '';
                },
                missing() {
                    if (optionSection.hidden || !toggle.checked || items.length) return false;
                    add.setCustomValidity(`${label}${isColor ? '을' : '를'} 하나 이상 입력하거나 '${label} 선택 받기'를 꺼 주세요.`);
                    add.reportValidity();
                    return true;
                },
            };
        });

        const showSection = () => { optionSection.hidden = category.value !== optionSection.dataset.optionSection; };
        category.addEventListener('change', showSection);
        showSection();
        // 임시 저장을 지우는 제출 처리보다 먼저 돌도록 캡처 단계에서 확인한다.
        form.addEventListener('submit', (event) => {
            groups.forEach((group) => group.commit());
            if (groups.some((group) => group.missing())) {
                event.preventDefault();
                event.stopImmediatePropagation();
            }
        }, true);
    }

    // 임시 저장을 불러온 뒤의 값으로 그려야 하므로 임시 저장 코드 다음에 둔다.
    document.querySelectorAll('[data-rating]').forEach((group) => {
        const inputs = [...group.querySelectorAll('input[type=radio]')];

        function updateRating() {
            const selected = inputs.find((input) => input.checked);
            inputs.forEach((input) => {
                input.closest('label').classList.toggle('off', Number(input.value) > Number(selected.value));
            });
            group.querySelector('[data-rating-score]').textContent = `${selected.value}.0`;
            group.querySelector('[data-rating-label]').textContent = selected.dataset.label;
        }

        inputs.forEach((input) => input.addEventListener('change', updateRating));
        updateRating();
    });

    document.querySelectorAll('[data-char-count]').forEach((field) => {
        const current = field.parentElement.querySelector('[data-char-current]');
        const update = () => { current.textContent = field.value.length; };
        field.addEventListener('input', update);
        update();
    });

    document.querySelectorAll('[data-password-rules]').forEach((rules) => {
        const input = document.getElementById(rules.dataset.passwordRules);
        const checks = {
            length: (value) => value.length >= 10,
            case: (value) => /[a-z]/.test(value) && /[A-Z]/.test(value),
            digit: (value) => /[0-9]/.test(value),
        };
        input.addEventListener('input', () => {
            rules.querySelectorAll('[data-rule]').forEach((rule) => {
                rule.classList.toggle('ok', checks[rule.dataset.rule](input.value));
            });
        });
    });

    document.querySelectorAll('[data-auto-submit]').forEach((select) => {
        select.addEventListener('change', () => {
            // 선택을 바꾸면 페이지가 다시 열리므로 작성 중인 내용을 먼저 저장한다.
            document.querySelectorAll('[data-draft]').forEach(saveDraft);
            select.form.requestSubmit();
        });
    });

    async function copyText(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch {
            return false;
        }
    }

    document.querySelectorAll('[data-copy]').forEach((button) => {
        const label = button.textContent;
        button.addEventListener('click', async () => {
            button.textContent = await copyText(button.dataset.copy) ? '복사했어요 ✓' : '복사하지 못했어요';
            setTimeout(() => { button.textContent = label; }, 2000);
        });
    });

    document.querySelectorAll('[data-share]').forEach((button) => {
        const status = button.parentElement.querySelector('[data-share-status]');
        button.addEventListener('click', async () => {
            const url = button.dataset.share;
            if (navigator.share) {
                try {
                    await navigator.share({ title: button.dataset.shareTitle, url });
                    return;
                } catch (error) {
                    if (error.name === 'AbortError') return;
                }
            }
            status.textContent = await copyText(url) ? '상품 링크를 복사했어요.' : `링크를 직접 복사해 주세요: ${url}`;
        });
    });

    const productForm = document.getElementById('product-form');
    if (productForm) {
        const todayStr = new Date().toISOString().split('T')[0];
        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');
        const pickupDateInput = document.getElementById('pickup_date');

        if (startDateInput) startDateInput.min = todayStr;
        if (endDateInput) endDateInput.min = todayStr;
        if (pickupDateInput) pickupDateInput.min = todayStr;

        // 시작일 선택 시 마감일의 최소 날짜(min)를 시작일로 동적 연동
        if (startDateInput && endDateInput) {
            startDateInput.addEventListener('change', () => {
                if (startDateInput.value) {
                    endDateInput.min = startDateInput.value;
                    if (endDateInput.value && endDateInput.value < startDateInput.value) {
                        endDateInput.value = startDateInput.value;
                    }
                }
            });
        }

        const priceDisplay = document.getElementById('price_display');
        const priceHidden = document.getElementById('price');
        if (priceDisplay && priceHidden) {
            const formatPrice = (val) => {
                const nums = String(val).replace(/[^0-9]/g, '');
                priceHidden.value = nums;
                priceDisplay.value = nums ? Number(nums).toLocaleString('ko-KR') : '';
            };
            formatPrice(priceDisplay.value);
            priceDisplay.addEventListener('input', (e) => formatPrice(e.target.value));
        }

        const pickupDate = document.getElementById('pickup_date');
        const pickupAmpm = document.getElementById('pickup_ampm');
        const pickupTime = document.getElementById('pickup_time');
        const pickupHidden = document.getElementById('pickup_datetime');

        if (pickupHidden && pickupHidden.value) {
            const parts = pickupHidden.value.split(' ');
            if (parts[0] && pickupDate) pickupDate.value = parts[0];
            if (parts[1] && pickupAmpm) pickupAmpm.value = parts[1];
            if (parts[2] && pickupTime) pickupTime.value = parts[2];
        }

        const updatePickupDatetime = () => {
            if (pickupDate && pickupDate.value && pickupHidden) {
                pickupHidden.value = `${pickupDate.value} ${pickupAmpm ? pickupAmpm.value : ''} ${pickupTime ? pickupTime.value : ''}`.trim();
            }
        };

        if (pickupDate) pickupDate.addEventListener('change', updatePickupDatetime);
        if (pickupAmpm) pickupAmpm.addEventListener('change', updatePickupDatetime);
        if (pickupTime) pickupTime.addEventListener('change', updatePickupDatetime);

        productForm.addEventListener('submit', (event) => {
            const invalidFields = [];
            const requiredFields = productForm.querySelectorAll('[required]');

            requiredFields.forEach((field) => {
                const targetEl = field.id === 'price' ? priceDisplay : field;
                if (!field.value.trim()) {
                    targetEl.classList.add('field-invalid');
                    invalidFields.push(targetEl);
                } else {
                    targetEl.classList.remove('field-invalid');
                }
            });

            // 마감일이 시작일보다 빠른 경우 예외 처리
            if (startDateInput && endDateInput && startDateInput.value && endDateInput.value) {
                if (endDateInput.value < startDateInput.value) {
                    endDateInput.classList.add('field-invalid');
                    if (!invalidFields.includes(endDateInput)) {
                        invalidFields.push(endDateInput);
                    }
                }
            }

            if (invalidFields.length > 0) {
                event.preventDefault();
                event.stopPropagation();

                invalidFields.sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top);
                const topErrorEl = invalidFields[0];

                topErrorEl.focus();
                topErrorEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        });
    }

    // 랭킹 카테고리 필터링
    const rankFilters = document.querySelectorAll('.rank-filters a');
    if (rankFilters.length > 0) {
        const rankItems = document.querySelectorAll('.rank-list li');

        rankFilters.forEach((tab) => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();

                const isAlreadyOn = tab.classList.contains('on');
                rankFilters.forEach((t) => t.classList.remove('on'));

                const targetCategory = isAlreadyOn ? null : (tab.dataset.rankTag || tab.textContent.trim());
                if (!isAlreadyOn) {
                    tab.classList.add('on');
                }

                rankItems.forEach((item) => {
                    const itemCat = item.dataset.category || '';
                    if (!targetCategory || itemCat === targetCategory) {
                        item.style.display = '';
                    } else {
                        item.style.display = 'none';
                    }
                });
            });
        });
    }