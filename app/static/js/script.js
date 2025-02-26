document.addEventListener("DOMContentLoaded", function () {
    getHistory().then(() => {
        hideLoading();
    });

    const dbSelector = document.getElementById('dbSelector');
    const responseElement = document.getElementById('response');
    const performanceGraph = document.getElementById('performanceGraph');
    const executionTable = document.getElementById('executionTable').querySelector("tbody");
    let loadingInterval;

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

    async function getHistory() {
        fetch('/history')
            .then(response => response.json())
            .then(data => {
                for (let i = 0; i < data.length; i++) {
                    updateExecutionTable(data[i]);
                }
            });
    }

    function showResponse(message) {
        message = JSON.stringify(message, null, 2);
        if (message.length > 10000) {
            message = message.substring(0, 10000) + "\n...";
        }
        responseElement.textContent = message;
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

        executionTable.scrollIntoView({behavior: "smooth", block: "end"});


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

    async function executeInsertOrSelect(endpoint, commandName, nbEntities) {
        const db = dbSelector.value;

        showLoading(commandName + " " + nbEntities + " (" + db + ")");
        const response = await fetch(`/${endpoint}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nb_entities: nbEntities, db_target: db})
        });
        hideLoading();

        const data = await response.json();

        showResponse(data);
        updateExecutionTable(data.command_history);
    }

    async function executeGlobalRequest(endpoint, commandName) {
        const db = dbSelector.value;
        showLoading(commandName + " (" + db + ")");
        const response = await fetch(`/${endpoint}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({db_target: db})
        });
        hideLoading();

        const data = await response.json();

        showResponse(data);
        updateExecutionTable(data.command_history);
    }

    async function executeSpecific1() {
        const db = dbSelector.value;
        const userId = document.getElementById('userIdSpecific1').value;
        const deepLevel = document.getElementById('deepLevelSpecific1').value;

        showLoading("Nb achats par produit depuis un user (profondeur : " + deepLevel + ") (" + db + ")");
        const response = await fetch(`/request/specific/1`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({db_target: db, user_id: userId, deep_level: deepLevel})
        });
        hideLoading();

        const data = await response.json();

        showResponse(data);
        updateExecutionTable(data.command_history);
    }

    async function executeSpecific2() {
        const db = dbSelector.value;
        const userId = document.getElementById('userIdSpecific2').value;
        const productId = document.getElementById('productIdSpecific2').value;
        const deepLevel = document.getElementById('deepLevelSpecific2').value;

        showLoading("Nb achats d'un produit depuis un user (profondeur : " + deepLevel + ") (" + db + ")");
        const response = await fetch(`/request/specific/2`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({db_target: db, user_id: userId, product_id: productId, deep_level: deepLevel})
        });
        hideLoading();

        const data = await response.json();

        showResponse(data);
        updateExecutionTable(data.command_history);
    }

    async function executeSpecific3() {
        const db = dbSelector.value;
        const productId = document.getElementById('productIdSpecific3').value;
        const deepLevel = document.getElementById('deepLevelSpecific3').value;

        showLoading("Nb achats d'un produit depuis un user (profondeur : " + deepLevel + ") (" + db + ")");
        const response = await fetch(`/request/specific/3`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({db_target: db, product_id: productId, deep_level: deepLevel})
        });
        hideLoading();

        const data = await response.json();

        showResponse(data);
        updateExecutionTable(data.command_history);
    }

    async function clearDB() {
        if (!confirm("Êtes-vous sûr de vouloir supprimer ?")) {
            return;
        }
        const db = dbSelector.value;
        fetch(`/clear`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({db_target: db})
        })
            .then(response => response.json())
            .then(data => {
                showResponse(data);
                updateExecutionTable(data.command_history);
            });
    }

    async function clearHistory() {
        if (!confirm("Êtes-vous sûr de vouloir supprimer l'historique ?")) {
            return;
        }
        const response = await fetch(`/clear_history`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });

        const data = await response.json();
        showResponse(data);
        location.reload();
    }

    async function getDBSize() {
        const db = dbSelector.value;
        const response = await fetch(`/size`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({db_target: db})
        });

        const data = await response.json();
        showResponse(data);
        updateExecutionTable(data.command_history);

        document.getElementById('nbUtilisateurs').textContent = data.size.nb_utilisateurs;
        document.getElementById('nbProduits').textContent = data.size.nb_produits;
        document.getElementById('nbAchats').textContent = data.size.nb_achats;
        document.getElementById('nbFollows').textContent = data.size.nb_follows;
    }

    function exportExcel() {
        let table = document.getElementById('executionTable');
        let wb = XLSX.utils.table_to_book(table, {sheet: 'Historique'});

        XLSX.writeFile(wb, 'historique_commandes.xlsx');
    }

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

    document.getElementById('createUsersBtn').addEventListener('click', () => executeInsertOrSelect('create_users', 'Insert Utilisateurs', document.getElementById('nbEntitiesInsert').value));
    document.getElementById('createProduitsBtn').addEventListener('click', () => executeInsertOrSelect('create_produits', 'Insert Produits', document.getElementById('nbEntitiesInsert').value));
    document.getElementById('createAchatsBtn').addEventListener('click', () => executeInsertOrSelect('create_achats', 'Insert Achats', document.getElementById('nbEntitiesInsert').value));
    document.getElementById('selectUsersBtn').addEventListener('click', () => executeInsertOrSelect('select_users', 'Select Utilisateurs', document.getElementById('nbEntitiesSelect').value));
    document.getElementById('selectProduitsBtn').addEventListener('click', () => executeInsertOrSelect('select_produits', 'Select Produits', document.getElementById('nbEntitiesSelect').value));

    document.getElementById('requestGlobalFollows').addEventListener('click', () => executeGlobalRequest('request/global/follows', document.getElementById('requestGlobalFollows').textContent));
    document.getElementById('requestGlobalAchats').addEventListener('click', () => executeGlobalRequest('request/global/achats', document.getElementById('requestGlobalAchats').textContent));
    document.getElementById('requestSpecific1').addEventListener('click', () => executeSpecific1());
    document.getElementById('requestSpecific2').addEventListener('click', () => executeSpecific2());
    document.getElementById('requestSpecific3').addEventListener('click', () => executeSpecific3());

    document.getElementById('dbSizeBtn').addEventListener('click', () => getDBSize());
    document.getElementById('dbClearBtn').addEventListener('click', () => clearDB());
    document.getElementById('clearHistory').addEventListener('click', () => clearHistory());
    document.getElementById('exportExcel').addEventListener('click', () => exportExcel());
});