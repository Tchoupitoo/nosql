document.addEventListener("DOMContentLoaded", function () {
    getHistory();
    const dbSelector = document.getElementById('dbSelector');
    const responseElement = document.getElementById('response');
    const performanceGraph = document.getElementById('performanceGraph');
    const executionTable = document.getElementById('executionTable').querySelector("tbody");
    let loadingInterval;

    function showLoading(commandLabel) {
        document.getElementById('loadingOverlay').style.display = 'flex';
        let startTime = Date.now();
        document.getElementById('loadingTime').textContent = "";
        document.getElementById('loadingTextCommande').textContent = commandLabel;

        loadingInterval = setInterval(() => {
            let elapsedTime = Math.floor((Date.now() - startTime) / 1000);
            if (elapsedTime < 60) {
                elapsedTime = elapsedTime + "s";
            } else if (elapsedTime < 3600) {
                elapsedTime = Math.floor(elapsedTime / 60) + "m " + (elapsedTime % 60) + "s";
            } else {
                elapsedTime = Math.floor(elapsedTime / 3600) + "h " + Math.floor((elapsedTime % 3600) / 60) + "m" + (elapsedTime % 60) + "s";
            }
            document.getElementById('loadingTime').textContent = elapsedTime;
        }, 1000);
    }

    function hideLoading() {
        clearInterval(loadingInterval);
        document.getElementById('loadingOverlay').style.display = 'none';
    }

    hideLoading();


    let postgresCommandCount = 0;
    let neo4jCommandCount = 0;

    let performanceData = {
        labels: [],
        datasets: [
            {
                label: 'PostgreSQL - Temps d\'exécution (ms)',
                data: [],
                borderColor: '#FFB38E',
                backgroundColor: '#FFDDAEAA',
                tension: 0.1,
                commandLabels: []
            },
            {
                label: 'Neo4j - Temps d\'exécution (ms)',
                data: [],
                borderColor: '#789DBC',
                backgroundColor: '#D4F6FFAA',
                tension: 0.1,
                commandLabels: []
            }
        ]
    };

    let chart = new Chart(performanceGraph, {
        type: 'line',
        data: performanceData,
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function (tooltipItem) {
                            const datasetIndex = tooltipItem.datasetIndex;
                            const commandLabel = performanceData.datasets[datasetIndex].commandLabels[tooltipItem.dataIndex];
                            return `${commandLabel} : ${tooltipItem.raw} ms`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Nombre de commandes exécutées'
                    },
                    ticks: {
                        beginAtZero: true
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Temps d\'exécution (ms)'
                    },
                    min: 0
                }
            }
        }
    });

    function getHistory() {
        fetch('/history')
            .then(response => response.json())
            .then(data => {
                console.log(data);
                for (let i = 0; i < data.length; i++) {
                    updateExecutionTable(data[i]);
                }
            });
    }

    function showResponse(message) {
        responseElement.textContent = JSON.stringify(message, null, 2);
    }

    function updateExecutionTable(data) {
        let newRow = executionTable.insertRow();

        let color = data.db_target === 'postgres' ? '#FFDDAE' : '#D4F6FF';
        newRow.style.backgroundColor = color;

        newRow.innerHTML = `
                <td>${data.date}</td>
                <td>${data.db_target}</td>
                <td>${data.command}</td>
                <td>${data.nb_entities != 0 ? data.nb_entities : ""}</td>
                <td>${data.execution_time}</td>
            `;

        executionTable.scrollIntoView({ behavior: "smooth", block: "end" });


        if (data.db_target === "postgres") {
            postgresCommandCount++;
            if (postgresCommandCount > neo4jCommandCount) {
                performanceData.labels.push(postgresCommandCount);
            }
            performanceData.datasets[0].data.push(data.execution_time);
            performanceData.datasets[0].commandLabels.push(`${data.command} ${data.nb_entities}`);

        } else {
            neo4jCommandCount++;
            if (neo4jCommandCount > postgresCommandCount) {
                performanceData.labels.push(neo4jCommandCount);
            }
            performanceData.datasets[1].data.push(data.execution_time);
            performanceData.datasets[1].commandLabels.push(`${data.command} ${data.nb_entities}`);
        }

        chart.update();
    }

    async function executeInsert(endpoint, commandName) {
        const db = dbSelector.value;
        const nbEntities = document.getElementById('nbEntities').value;

        showLoading(commandName + " " + nbEntities + " (" + db + ")");
        const response = await fetch(`/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nb_entities: nbEntities, db_target: db })
        });
        hideLoading();

        const data = await response.json();

        showResponse(data);
        updateExecutionTable(data.command_history);
    }

    async function executeRequest(endpoint, commandName) {
        const db = dbSelector.value;
        showLoading(commandName + " (" + db + ")");
        const response = await fetch(`/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ db_target: db })
        });
        hideLoading();

        const data = await response.json();

        showResponse(data);
        updateExecutionTable(data.command_history);
    }

    document.getElementById('request1').addEventListener('click', () => executeRequest('request1', document.getElementById('request1').textContent));
    document.getElementById('request2').addEventListener('click', () => executeRequest('request2', document.getElementById('request2').textContent));
    document.getElementById('request3').addEventListener('click', () => executeRequest('request3', document.getElementById('request3').textContent));
    document.getElementById('request4').addEventListener('click', () => executeRequest('request4', document.getElementById('request4').textContent));
    document.getElementById('request5').addEventListener('click', () => executeRequest('request5', document.getElementById('request5').textContent));
    document.getElementById('request6').addEventListener('click', () => executeRequest('request6', document.getElementById('request6').textContent));

    document.getElementById('createUsersBtn').addEventListener('click', () => executeInsert('create_users', 'Insert Utilisateurs'));
    document.getElementById('createProduitsBtn').addEventListener('click', () => executeInsert('create_produits', 'Insert Produits'));
    document.getElementById('createAchatsBtn').addEventListener('click', () => executeInsert('create_achats', 'Insert Achats'));

    // Gestion de la taille de la base de données
    document.getElementById('dbSizeBtn').addEventListener('click', async () => {
        const db = dbSelector.value;
        const response = await fetch(`/size`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ db_target: db })
        });

        const data = await response.json();
        showResponse(data);
        updateExecutionTable(data.command_history);

        document.getElementById('nbUtilisateurs').textContent = data.size.nb_utilisateurs;
        document.getElementById('nbProduits').textContent = data.size.nb_produits;
        document.getElementById('nbAchats').textContent = data.size.nb_achats;
        document.getElementById('nbFollowers').textContent = data.size.nb_followers;
    });

    document.getElementById('dbClearBtn').addEventListener('click', async () => {
        if (!confirm("Êtes-vous sûr de vouloir supprimer ?")) {
            return;
        }
        const db = dbSelector.value;
        const response = await fetch(`/clear`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ db_target: db })
        });

        const data = await response.json();
        showResponse(data);
        updateExecutionTable(data.command_history);
    });

    document.getElementById('exportExcel').addEventListener('click', () => {
        let table = document.getElementById('executionTable');
        let wb = XLSX.utils.table_to_book(table, { sheet: 'Historique' });

        XLSX.writeFile(wb, 'historique_commandes.xlsx');
    });
});