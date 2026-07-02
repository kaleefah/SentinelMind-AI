console.log("SentinelMind frontend loaded");

function scrollToSubmit() {
    const el = document.getElementById("submit-section");
    if (el) {
        el.scrollIntoView({ behavior: "smooth" });
    }
}

async function submitIncident() {

    const title = document.getElementById("title").value.trim();
    const description = document.getElementById("description").value.trim();
    const system = document.getElementById("system").value.trim();

    const resultDiv = document.getElementById("result");
    const memoryDiv = document.getElementById("memory-result");
    const btn = document.getElementById("analyze-btn");

    if (!title || !description) {
        resultDiv.innerHTML =
        `<p style="color:#ff6b6b;">
        Please enter Title and Description.
        </p>`;
        return;
    }

    btn.disabled = true;
    btn.textContent = "Analysing...";

    resultDiv.innerHTML =
        "<p>⏳ Running AI analysis...</p>";

    memoryDiv.innerHTML =
        "<p>🧠 Searching organizational memory...</p>";

    try {

        //-----------------------------
        // AI Analysis
        //-----------------------------

        const response = await fetch("http://127.0.0.1:8000/incident", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                title,
                description,
                system
            })

        });

        const data = await response.json();

        resultDiv.innerHTML = `
            <h3>🧠 AI Analysis</h3>

            <p><b>Category:</b> ${data.result.category}</p>

            <p><b>Severity:</b> ${data.result.severity}</p>

            <p><b>Recommendation:</b></p>

            <div class="recommendation">
                ${data.result.recommendation}
            </div>
        `;

        //-----------------------------
        // Search Similar Incidents
        //-----------------------------

        const memoryResponse = await fetch(
            `http://127.0.0.1:8000/incident/similar?q=${encodeURIComponent(description)}`
        );

        const memory = await memoryResponse.json();

        if (memory.count === 0) {

            memoryDiv.innerHTML = `
                <h3>🧠 Organizational Memory</h3>

                <p>No similar incidents found.</p>
            `;

        } else {

            let html = "<h3>🧠 Organizational Memory</h3>";

            memory.incidents.forEach(incident => {

                html += `

                <div class="memory-card">

                    <h4>${incident.title}</h4>

                    <p><b>Severity:</b> ${incident.severity}</p>

                    <p><b>Category:</b> ${incident.category}</p>

                    <p>${incident.description}</p>

                </div>

                <hr>

                `;

            });

            memoryDiv.innerHTML = html;

        }

    }

    catch(err){

        resultDiv.innerHTML =

        `<p style="color:red;">
        ${err.message}
        </p>`;

    }

    finally{

        btn.disabled = false;

        btn.textContent = "Analyze Incident →";

    }

}