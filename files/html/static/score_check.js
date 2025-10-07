function updateOtherState(selectEl) {
    const otherInput = document.getElementById(selectEl.id.replace("_name", "_other"));

    if (selectEl.value === "other") {
        otherInput.disabled = false;
        otherInput.required = true;
        otherInput.placeholder = "ゲストの名前を入力";
    } else {
        otherInput.disabled = true;
        otherInput.required = false;
        otherInput.placeholder = "---";
        otherInput.value = "";
    }
}

// セレクトの初期化とイベント登録
const selects = document.querySelectorAll("select[id$='_name']");
selects.forEach(selectEl => {
    selectEl.addEventListener("change", () => updateOtherState(selectEl));
    updateOtherState(selectEl); // 初期状態
});

// リセット後に再適用
document.getElementById("player_select").addEventListener("reset", function() {
    setTimeout(() => {
    selects.forEach(selectEl => updateOtherState(selectEl));
        updateChecks();
    }, 0);
});

function evaluateExpression(expr) {
    try {
        if (!expr.trim()) return 0;
        return Function('"use strict";return (' + expr + ')')();
    } catch (e) {
        return 0; // 無効な式は0扱い
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const appElement = document.getElementById("app");
    const originPoint = appElement.dataset.originPoint;

    function updateChecks() {
        const selects = document.querySelectorAll(".name-select");
        const others  = document.querySelectorAll(".name-other");
        const scores  = document.querySelectorAll(".score-input");

        // --- 名前のユニークチェック ---
        let names = [];
        selects.forEach((sel, i) => {
            if (sel.value === "other") {
                names.push(others[i].value.trim());
            } else {
                names.push(sel.value.trim());
            }
        });

        let hasDuplicate = new Set(names).size !== names.length;
        document.getElementById("nameError").textContent =
        hasDuplicate ? "名前に重複があります" : "";
        // --- 点数合計チェック ---
        let total = 0;
        scores.forEach(sc => {
            total += evaluateExpression(sc.value);
        });

        // 供託チェック
        let diff = (originPoint * 4) - total;
        document.getElementById("scoreCheck").textContent = `供託：${diff}`;
    };

    // プルダウンのother制御 + チェック
    document.querySelectorAll(".name-select").forEach((sel, i) => {
        sel.addEventListener("change", () => {
            updateChecks();
        });
    });

    // other入力、点数入力のフォーカスアウトでチェック
    document.querySelectorAll(".name-other, .score-input").forEach(el => {
        el.addEventListener("blur", updateChecks);
    });

    // 初期チェック
    updateChecks();
});
