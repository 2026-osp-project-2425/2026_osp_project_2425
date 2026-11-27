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
                message.textContent = '아이디를 확인하지 못했습니다. 다시 시도해 주십시오.';
            }
        });
    });

    async function draftRequest(kind, method = 'GET', data) {
        const version = method === 'DELETE' ? `?version=${encodeURIComponent(data)}` : '';
        const response = await fetch(`/api/drafts/${kind}${version}`, {
            method,
            ...(method === 'PUT' ? {headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)} : {}),
        });
        if (response.status === 204) return null;
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || '임시저장 요청에 실패했습니다.');
        return result.draft;
    }

    document.querySelectorAll('[data-draft]').forEach((form) => {
        const kind = form.dataset.draft;
        const status = form.querySelector('[data-draft-status]');
        const button = form.querySelector('[data-save-draft]');
        const version = form.elements.draft_version;
        const fields = [...form.elements].filter((field) =>
            field.name && !field.readOnly && field !== version && field.type !== 'file');
        const productId = form.elements.product_id?.value;
        let saved = null;
        let edited = false;
        form.addEventListener('input', () => { edited = true; });

        function remember(draft) {
            saved = draft;
            version.value = draft.updated_at;
        }

        draftRequest(kind).then((draft) => {
            if (!draft || edited || (kind === 'review' && draft.data.product_id !== productId)) return;
            fields.forEach((field) => {
                if (field.name === 'product_id' || !Object.hasOwn(draft.data, field.name)) return;
                const value = draft.data[field.name];
                if (field.type === 'checkbox') field.checked = value === true;
                else if (field.type === 'radio') field.checked = field.value === String(value);
                else field.value = value;
            });
            remember(draft);
            form.dispatchEvent(new Event('draft-restored'));
            status.textContent = '임시저장 내용을 불러왔습니다. 사진은 다시 선택해야 합니다.';
        }).catch((error) => { status.textContent = error.message; });

        button.addEventListener('click', async () => {
            button.disabled = true;
            try {
                const latest = await draftRequest(kind);
                if (latest && latest.updated_at !== saved?.updated_at
                    && !window.confirm('이전에 임시 저장한 글을 덮어쓰시겠습니까?')) return;
                const values = {};
                fields.forEach((field) => {
                    if (field.type === 'checkbox') values[field.name] = field.checked;
                    else if (field.type !== 'radio' || field.checked) values[field.name] = field.value;
                });
                remember(await draftRequest(kind, 'PUT', values));
                status.textContent = '임시 저장했습니다. 사진은 저장되지 않습니다.';
            } catch (error) {
                status.textContent = error.message;
            } finally {
                button.disabled = false;
            }
        });
    });

    // 상품 등록의 사이즈·색상 입력. 숨긴 textarea에 한 줄에 하나씩 담아 보내므로 임시 저장도 그대로 된다.
    const COLOR_HINTS = { 블랙: '#17212c', 화이트: '#ffffff', 아이보리: '#f4f0e4', 그레이: '#9a9ea3', 차콜: '#3a3d40', 네이비: '#1f2a44', 블루: '#2b5ea7', 그린: '#2f6b4f', 레드: '#b3261e', 핑크: '#f2b8c6', 베이지: '#d9c9a8', 브라운: '#6b4a32' };
    const optionSection = document.querySelector('[data-option-section]');
    if (optionSection) {
        const form = optionSection.closest('form');
        const groups = [...optionSection.querySelectorAll('[data-option-group]')].map((group) => {
            const isColor = group.dataset.optionGroup === 'color';
            const store = group.querySelector('[data-option-store]');
            const list = group.querySelector('[data-option-tags]');
            const add = group.querySelector('[data-option-add]');
            const toggle = group.querySelector('[data-option-toggle]');
            const body = group.querySelector('[data-option-body]');
            const label = isColor ? '색상' : group.dataset.optionGroup === 'custom' ? '기타 옵션' : '사이즈';
            let items;
            function restoreOptions() {
                items = store.value.split('\n').map((line) => line.trim()).filter(Boolean).map((line) => {
                    const cut = line.lastIndexOf('|');
                    return isColor && cut > 0 ? { name: line.slice(0, cut), hex: line.slice(cut + 1) } : { name: line, hex: '' };
                });
                body.hidden = !toggle.checked;
                render();
            }

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
            restoreOptions();
            form.addEventListener('draft-restored', restoreOptions);

            return {
                // 입력만 하고 Enter를 누르지 않은 값도 제출할 때 함께 담는다.
                commit() {
                    if (add.value.trim()) addNames(add.value.split(','));
                    add.value = '';
                },
                missing() {
                    if (optionSection.hidden || !toggle.checked || items.length) return false;
                    add.setCustomValidity(`${label}${isColor ? '을' : '를'} 하나 이상 입력하거나 '${label} 선택 받기'를 꺼 주십시오.`);
                    add.reportValidity();
                    return true;
                },
            };
        });

        form.querySelector('[data-save-draft]')?.addEventListener('click', () => {
            groups.forEach((group) => group.commit());
        }, true);
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
        group.closest('form').addEventListener('draft-restored', updateRating);
        updateRating();
    });

    document.querySelectorAll('[data-char-count]').forEach((field) => {
        const current = field.parentElement.querySelector('[data-char-current]');
        const update = () => { current.textContent = field.value.length; };
        field.addEventListener('input', update);
        field.closest('form')?.addEventListener('draft-restored', update);
        update();
    });

    // 문의 및 답변 글자 수 표시
    document.querySelectorAll('[data-count-target]').forEach((field) => {
        const current = document.getElementById(field.dataset.countTarget);
        if (!current) return;
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
            button.textContent = await copyText(button.dataset.copy) ? '복사 완료 ✓' : '복사 실패';
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
            status.textContent = await copyText(url) ? '상품 링크를 복사했습니다.' : `링크를 직접 복사해 주십시오: ${url}`;
        });
    });

    const productForm = document.getElementById('product-form');
    if (productForm) {
        const todayStr = new Date(Date.now() + 9 * 60 * 60 * 1000).toISOString().split('T')[0];

        const startDateInput = document.getElementById('start_date');
        const endDateInput = document.getElementById('end_date');
        const pickupDateInput = document.getElementById('pickup_date');

        const originalStart = productForm.dataset.originalStart;
        const minStart = originalStart && originalStart < todayStr ? originalStart : todayStr;
        const invalidStart = (value) => value < todayStr && value !== originalStart;
        if (startDateInput) startDateInput.min = minStart;
        if (endDateInput) endDateInput.min = startDateInput.value || todayStr;
        function updatePickupMinimum() {
            pickupDateInput.min = endDateInput.value || todayStr;
        }
        endDateInput.addEventListener('change', updatePickupMinimum);
        productForm.addEventListener('draft-restored', () => {
            endDateInput.min = startDateInput.value || todayStr;
            updatePickupMinimum();
        });
        updatePickupMinimum();

        // 오늘 이전 날짜 입력 차단 + 마감일 최소 날짜(min) 연동
        if (startDateInput) {
            startDateInput.addEventListener('change', () => {
                if (startDateInput.value && invalidStart(startDateInput.value)) {
                    alert('시작일은 오늘 이전 날짜를 선택할 수 없습니다.');
                    startDateInput.value = todayStr;
                }

                const minEndDate = startDateInput.value || todayStr;
                if (endDateInput) {
                    endDateInput.min = minEndDate;
                    if (endDateInput.value && endDateInput.value < minEndDate) {
                        endDateInput.value = minEndDate;
                    }
                    updatePickupMinimum();
                }
            });
        }

        // 키보드 입력 시에도 마감일 오늘 이전 날짜 차단
        if (endDateInput) {
            endDateInput.addEventListener('change', () => {
                const minEndDate = (startDateInput && startDateInput.value) ? startDateInput.value : todayStr;
                if (endDateInput.value && endDateInput.value < minEndDate) {
                    endDateInput.value = minEndDate;
                }
            });
        }

        if (pickupDateInput) {
            pickupDateInput.addEventListener('change', () => {
                if (pickupDateInput.value && pickupDateInput.value < pickupDateInput.min) {
                    pickupDateInput.value = pickupDateInput.min;
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
            formatPrice(priceHidden.value);
            productForm.addEventListener('draft-restored', () => formatPrice(priceHidden.value));
            priceDisplay.addEventListener('input', (e) => formatPrice(e.target.value));
        }

        const pickupDate = document.getElementById('pickup_date');
        const pickupAmpm = document.getElementById('pickup_ampm');
        const pickupTime = document.getElementById('pickup_time');
        const pickupHidden = document.getElementById('pickup_datetime');

        function restorePickup() {
            const [date, period, time] = pickupHidden.value.split(' ');
            pickupDate.value = date || '';
            pickupAmpm.value = period || '오전';
            pickupTime.value = time || '12:00';
        }
        restorePickup();
        productForm.addEventListener('draft-restored', restorePickup);

        const updatePickupDatetime = () => {
            pickupHidden.value = pickupDate.value
                ? `${pickupDate.value} ${pickupAmpm.value} ${pickupTime.value}`
                : '';
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

            // 시작일이 오늘 이전인 경우 예외 처리
            if (startDateInput && startDateInput.value && invalidStart(startDateInput.value)) {
                startDateInput.classList.add('field-invalid');
                if (!invalidFields.includes(startDateInput)) {
                    invalidFields.push(startDateInput);
                }
            }

            // 마감일이 시작일(또는 오늘)보다 빠른 경우 예외 처리
            if (endDateInput && endDateInput.value) {
                const minEndDate = (startDateInput && startDateInput.value) ? startDateInput.value : todayStr;
                if (endDateInput.value < minEndDate) {
                    endDateInput.classList.add('field-invalid');
                    if (!invalidFields.includes(endDateInput)) {
                        invalidFields.push(endDateInput);
                    }
                }
            }

            // 픽업일이 오늘 이전인 경우 예외 처리
            if (pickupDateInput && pickupDateInput.value && pickupDateInput.value < pickupDateInput.min) {
                pickupDateInput.classList.add('field-invalid');
                if (!invalidFields.includes(pickupDateInput)) {
                    invalidFields.push(pickupDateInput);
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

    const draftContainer = document.getElementById('draft-list-container');
    if (draftContainer) {
        const count = document.getElementById('draft-count');
        const empty = draftContainer.querySelector('.table-empty');
        const kinds = [['product', '상품 등록'], ['review', '리뷰 작성']];
        Promise.allSettled(kinds.map(async ([kind, label]) => {
            const draft = await draftRequest(kind);
            if (!draft) return;
            const item = document.getElementById('draft-list-item').content.firstElementChild.cloneNode(true);
            item.querySelector('.order-name').textContent = (kind === 'product' ? draft.data.name : draft.data.title) || label;
            item.querySelector('.order-meta').textContent = label;
            item.querySelector('a').href = draft.resume_url;
            const button = item.querySelector('button');
            button.addEventListener('click', async () => {
                button.disabled = true;
                try {
                    await draftRequest(kind, 'DELETE', draft.updated_at);
                    item.remove();
                    updateCount();
                } catch (error) {
                    item.querySelector('[role="status"]').textContent = error.message;
                    button.disabled = false;
                }
            });
            draftContainer.append(item);
        })).then((results) => {
            if (results.some((result) => result.status === 'rejected')) empty.textContent = '일부 임시저장 글을 불러오지 못했습니다.';
            updateCount();
        });

        function updateCount() {
            const total = draftContainer.querySelectorAll('.order-item').length;
            count.textContent = `(${total})`;
            empty.hidden = total > 0 && empty.textContent === '임시 저장한 글이 없습니다.';
        }
    }

    // 공지사항 수정 버튼 클릭 처리
    const noticeForm = document.querySelector('.notice-form');

    if (noticeForm) {
        const titleInput = document.getElementById('notice-title');
        const contentInput = document.getElementById('notice-body');
        const editIdInput = document.getElementById('notice-edit-id');
        const importantInput = noticeForm.querySelector('input[name="important"]');
        const submitButton = noticeForm.querySelector('button[type="submit"]');

        const cancelButton = document.createElement('button');
        cancelButton.type = 'button';
        cancelButton.className = 'line-btn';
        cancelButton.textContent = '수정 취소';
        cancelButton.hidden = true;
        submitButton.after(cancelButton);

        function resetNoticeForm() {
            noticeForm.reset();
            editIdInput.value = '';
            editIdInput.disabled = true;
            submitButton.textContent = '공지 등록';
            cancelButton.hidden = true;
        }

        document.querySelectorAll('[data-notice-edit]').forEach(btn => {
            btn.addEventListener('click', () => {
                titleInput.value = btn.dataset.title || '';
                contentInput.value = btn.dataset.content || '';
                importantInput.checked = btn.dataset.important === 'true';

                editIdInput.value = btn.dataset.noticeEdit;
                editIdInput.disabled = false;

                submitButton.textContent = '공지 수정 완료';
                cancelButton.hidden = false;

                titleInput.focus();
                titleInput.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            });
        });

        cancelButton.addEventListener('click', resetNoticeForm);
    }
    
    const reviewLikeButton = document.getElementById("review-like-button");

if (reviewLikeButton) {
    const message = document.getElementById("review-like-message");
    const url = reviewLikeButton.dataset.url;
    let liked = false;

    function showLikeState(value) {
        liked = value;
        reviewLikeButton.textContent =
            liked ? "♥ 좋아요 취소" : "♡ 좋아요";
    }

    async function loadLikeState() {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error();

            const data = await response.json();
            showLikeState(data.liked);
            reviewLikeButton.disabled = false;
        } catch {
            message.textContent = "좋아요 상태를 불러오지 못했습니다.";
        }
    }

    reviewLikeButton.addEventListener("click", async () => {
        reviewLikeButton.disabled = true;
        message.textContent = "";

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ liked: !liked })
            });

            if (!response.ok) throw new Error();

            const data = await response.json();
            showLikeState(data.liked);
        } catch {
            message.textContent = "좋아요 처리에 실패했습니다.";
        } finally {
            reviewLikeButton.disabled = false;
        }
    });

    loadLikeState();
}
document.querySelectorAll("button.review-like-small").forEach((button) => {
    const message = button.parentElement.querySelector(".review-like-message");
    const url = button.dataset.url;
    let liked = false;

    function showLikeState(value) {
        liked = value;
        button.textContent = liked ? "♥ 좋아요" : "♡ 좋아요";
        button.classList.toggle("is-liked", liked);
        button.setAttribute("aria-pressed", String(liked));
    }

    async function loadLikeState() {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error();

            const data = await response.json();
            showLikeState(data.liked);
            button.disabled = false;
        } catch {
            message.textContent = "좋아요를 불러오지 못했습니다.";
        }
    }

    button.addEventListener("click", async () => {
        button.disabled = true;
        message.textContent = "";

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ liked: !liked })
            });

            if (!response.ok) throw new Error();

            const data = await response.json();
            showLikeState(data.liked);
        } catch {
            message.textContent = "다시 시도해 주십시오.";
        } finally {
            button.disabled = false;
        }
    });

    loadLikeState();
});

// 상품 상세 > 문의 작성 폼 열기 및 닫기
document.querySelectorAll('[data-qna-toggle]').forEach((button) => {
    const form = document.getElementById(button.getAttribute('aria-controls'));
    if (!form) return;
    button.addEventListener('click', () => {
        const open = form.hidden;
        form.hidden = !open;
        button.setAttribute('aria-expanded', String(open));
        button.textContent = open ? '작성 취소' : '✎ 문의하기';
        if (open) form.querySelector('textarea').focus();
    });
});

// 상품 상세 > 문의 더보기
document.querySelectorAll('[data-qna-list]').forEach((list) => {
    const rows = [...list.querySelectorAll('[data-qna-row]')];
    const more = list.parentElement.querySelector('[data-qna-more]');
    const size = Number(list.dataset.pageSize) || 5;
    let shown = 0;
    const showMore = () => {
        shown += size;
        rows.forEach((row, index) => { row.hidden = index >= shown; });
        if (more) more.hidden = shown >= rows.length;
    };
    if (more) more.addEventListener('click', showMore);
    showMore();

    // 첫 번째 답변 완료 문의 자동 펼치기
    const firstAnswered = rows.find((row) => !row.hidden && row.querySelector('.status-chip.done'));
    if (firstAnswered) firstAnswered.open = true;
});