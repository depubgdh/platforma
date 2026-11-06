const tg = window.Telegram?.WebApp;

tg?.ready();
tg?.expand();

const initData = tg?.initData || "";

const $ = id => document.getElementById(id);

let currentVideo = null;


function toast(s) {
    const e = $("toast");

    e.textContent = s;
    e.classList.add("show");

    setTimeout(
        () => e.classList.remove("show"),
        2500
    );
}


async function api(path, method = "GET", body = null) {
    const r = await fetch(path, {
        method,
        headers: {
            "Content-Type": "application/json",
            "X-Telegram-Init-Data": initData
        },
        body: body ? JSON.stringify(body) : undefined
    });

    const d = await r.json().catch(
        () => ({ detail: "Server javobi xato" })
    );

    if (!r.ok) {
        throw Error(d.detail || "Xatolik");
    }

    return d;
}


function esc(s) {
    return String(s ?? "").replace(
        /[&<>"']/g,
        c => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#39;"
        }[c])
    );
}


function history(rows) {
    $("history").innerHTML = rows.length
        ? rows.map(x => `
            <div class="history-row">
                <span>${esc(x.note || x.kind)}</span>
                <b class="${x.amount >= 0 ? "positive" : ""}">
                    ${x.amount >= 0 ? "+" : ""}
                    ${Number(x.amount).toFixed(2)} 🔆
                </b>
            </div>
        `).join("")
        : "Hozircha yozuv yo‘q";
}


function tasks(rows, done) {
    $("tasks").innerHTML = rows.length
        ? rows.map(t => `
            <div class="task">
                <div class="task-info">
                    <b>${esc(t.title)}</b>
                    <small>${esc(t.description || "Demo topshiriq")}</small>
                </div>

                <span class="reward">
                    +${Number(t.reward).toFixed(2)} 🔆
                </span>

                <button
                    data-id="${t.id}"
                    ${done.includes(t.id) ? "disabled" : ""}
                >
                    ${done.includes(t.id) ? "Bajarildi" : "Bajarish"}
                </button>
            </div>
        `).join("")
        : "Topshiriqlar hozircha mavjud emas";

    document.querySelectorAll("[data-id]").forEach(b => {
        b.onclick = () => complete(
            Number(b.dataset.id),
            b
        );
    });
}


function setVideo(v) {
    currentVideo = v;

    $("videoTitle").textContent = v.title;

    $("player").innerHTML = `
        <div id="placeholder">
            ▶
            <small>Videoni boshlash tugmasini bosing</small>
        </div>
    `;
}


async function load() {
    try {
        const d = await api("/api/me");

        $("balance").textContent =
            Number(d.user.balance).toFixed(2) + " 🔆";

        tasks(d.tasks, d.completed_tasks);
        history(d.transactions);

        if (d.video) {
            setVideo(d.video);
        } else {
            $("videoTitle").textContent =
                "Hozircha video mavjud emas";

            $("player").innerHTML = `
                <div id="placeholder">
                    🎬
                    <small>Admin video qo‘shishini kuting</small>
                </div>
            `;
        }

    } catch (e) {
        toast(e.message);
        $("videoTitle").textContent =
            "Ilovaga Telegram orqali kiring";
    }
}


$("start").onclick = () => {
    if (!currentVideo) {
        return toast("Video mavjud emas");
    }

    $("player").innerHTML = `
        <iframe
            src="https://www.youtube-nocookie.com/embed/${encodeURIComponent(currentVideo.youtube_id)}?autoplay=1&rel=0"
            title="YouTube video"
            allow="accelerometer;autoplay;clipboard-write;encrypted-media;gyroscope;picture-in-picture;web-share"
            allowfullscreen>
        </iframe>
    `;
};


$("next").onclick = async () => {
    try {
        const d = await api("/api/me");

        if (d.video) {
            setVideo(d.video);
        } else {
            toast("Video yo‘q");
        }

    } catch (e) {
        toast(e.message);
    }
};


async function complete(id, b) {
    b.disabled = true;

    try {
        const d = await api(
            "/api/tasks/complete",
            "POST",
            { task_id: id }
        );

        toast(`+${d.reward} 🔆 demo ball olindi`);

        await load();

    } catch (e) {
        toast(e.message);
        b.disabled = false;
    }
}


$("bulldrop").onclick = async () => {
    try {
        const d = await api(
            "/api/bulldrop/demo-token",
            "POST"
        );

        toast(
            "Demo token yaratildi; Bulldrop serveriga ulash kerak."
        );

        console.info("Temporary demo token", d.token);

    } catch (e) {
        toast(e.message);
    }
};


$("goTasks").onclick = () => {
    $("tasks").scrollIntoView({ behavior: "smooth" });
};

$("goBalance").onclick = () => {
    $("balance").scrollIntoView({ behavior: "smooth" });
};

$("goProfile").onclick = () => {
    $("history").scrollIntoView({ behavior: "smooth" });
};

$("profile").onclick = () => {
    $("history").scrollIntoView({ behavior: "smooth" });
};


load();
