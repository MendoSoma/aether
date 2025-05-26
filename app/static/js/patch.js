let firstSelection = null;
const connections = new Map();
const nodeConnections = new Map();
const universeConnections = new Map();
let selectedUniverseId = null;
let selectedFixtureFile = null;

async function updateNodes(showLoading = false) {
  const nodesUl = document.getElementById('nodes_ul');

  if (showLoading) {
    nodesUl.innerHTML = `
            <li class="flex justify-center items-center py-4">
                <svg class="animate-spin h-8 w-8 text-gray-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            </li>
        `;
  }

  try {
    const response = await fetch('/api/nodes');
    const nodes = await response.json();
    nodesUl.innerHTML = nodes.length === 0 
      ? '<li>No ArtNet nodes found.</li>'
      : nodes.map((node, index) => `
        <li class="list-item-container selectable flex justify-between items-center" data-node-id="{{ loop.index0 }}">
            <div>
                <p class="font-medium">${node.name || 'Unknown Node'}</p>
                <p class="text-sm text-gray-400">
                    <span data-type="node-ip">${node.ip}</span></br>
                    <span data-type="node-universe-spots">${node.universe_count || 'Unknown'} Universe Ports</span></br>
                    <span data-type="node-universe-count">0 Universes Patched</span>
                </p>
            </div>
            <div class="status-indicator online" data-type="cnx_node" data-port-count="${node.universe_count || -1}"></div>
        </li>
      `).join('');

    // Setup connection listeners after nodes are loaded
    setupConnectionListeners();
  } catch (error) {
    console.error('Error fetching nodes:', error);
    nodesUl.innerHTML = '<li>Error fetching nodes.</li>';
  }
}

function setupConnectionListeners() {
  const connectableItems = document.querySelectorAll('[data-type="cnx_node"], [data-type="cnx_universe"]');
  connectableItems.forEach(item => {
    // Remove existing listener to prevent duplicates
    item.removeEventListener('click', handleConnectionClick);
    item.addEventListener('click', handleConnectionClick);
  });

  // Re-attach click listeners for connection paths
  const svg = document.getElementById('connection-svg');
  const connectionPaths = svg.querySelectorAll('[data-connection-key]');
  connectionPaths.forEach(path => {
    path.removeEventListener('click', handleConnectionPathClick);
    path.addEventListener('click', handleConnectionPathClick);
  });
}

function handleConnectionClick(event) {
  const item = event.currentTarget; // Already targeting the correct div

  if (firstSelection === null) {
    firstSelection = item; // Fix: Assign the item, not a string
    item.classList.add('selected');
  } else {
    if (firstSelection !== item && firstSelection.getAttribute('data-type') !== item.getAttribute('data-type')) {
      const sourceType = firstSelection.getAttribute('data-type');
      const targetType = item.getAttribute('data-type');
      const sourceDiv = firstSelection;
      const targetDiv = item;
      const sourceParent = firstSelection.closest('li');
      const targetParent = item.closest('li');
      const sourceId = sourceType === 'cnx_node' 
        ? sourceParent.getAttribute('data-node-id') 
        : sourceParent.getAttribute('data-universe-id');
      const targetId = targetType === 'cnx_universe' 
        ? targetParent.getAttribute('data-universe-id') 
        : targetParent.getAttribute('data-node-id');

      const nodeId = sourceType === 'cnx_node' ? sourceId : targetId;
      const universeId = sourceType === 'cnx_universe' ? sourceId : targetId;

      if (universeConnections.has(universeId)) {
        alert('This universe is already connected to a node.');
        clearSelection();
        return;
      }

      const nodeConnectionCount = nodeConnections.get(nodeId) || 0;
      const nodeDiv = sourceType === 'cnx_node' ? sourceDiv : targetDiv;
      const portCount = parseInt(nodeDiv.getAttribute('data-port-count')) || -1;
      if (portCount !== -1 && nodeConnectionCount >= portCount) {
        alert(`This node has reached its maximum of ${portCount} universe connections.`);
        clearSelection();
        return;
      }

      const connectionKey = `${nodeId}-${universeId}`;
      if (!connections.has(connectionKey)) {
        connections.set(connectionKey, { source: sourceDiv, target: targetDiv, path: null });
        nodeConnections.set(nodeId, nodeConnectionCount + 1);
        universeConnections.set(universeId, nodeId);

        // Update text for node
        const nodeLi = sourceType === 'cnx_node' ? sourceParent : targetParent;
        const nodeCountSpan = nodeLi.querySelector('[data-type="node-universe-count"]');
        nodeCountSpan.textContent = `${nodeConnectionCount + 1} Universe${nodeConnectionCount + 1 === 1 ? '' : 's' } Patched`;

        // Update text for universe
        const universeLi = sourceType === 'cnx_universe' ? sourceParent : targetParent;
        const universeNodeSpan = universeLi.querySelector('[data-type="universe-node"]');
        const nodeName = nodeLi.querySelector('.font-medium').textContent;
        universeNodeSpan.textContent = nodeName;

        // Swap empty for online on universe indicator
        if (targetType === 'cnx_universe') {
          targetDiv.classList.remove('empty');
          targetDiv.classList.add('online');
        } else if (sourceType === 'cnx_universe') {
          sourceDiv.classList.remove('empty');
          sourceDiv.classList.add('online');
        }

        const svg = document.getElementById('connection-svg');
        drawConnection(sourceDiv, targetDiv, svg, connectionKey);
      }
    }
    clearSelection();
  }
}

function handleConnectionPathClick(e) {
  if (e.ctrlKey) {
    const path = e.target;
    const key = path.getAttribute('data-connection-key');
    removeConnection(key, path);
  }
}

function drawConnection(source, target, svg, connectionKey) {
  const sourceRect = source.getBoundingClientRect();
  const targetRect = target.getBoundingClientRect();
  const svgRect = svg.getBoundingClientRect();

  const sourceX = sourceRect.left + sourceRect.width / 2 - svgRect.left;
  const sourceY = sourceRect.top + sourceRect.height / 2 - svgRect.top;
  const targetX = targetRect.left + targetRect.width / 2 - svgRect.left;
  const targetY = targetRect.top + targetRect.height / 2 - svgRect.top;

  const midX = (sourceX + targetX) / 2;
  const midY = (sourceY + targetY) / 2 + 40;

  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d', `M ${sourceX} ${sourceY} Q ${midX} ${midY} ${targetX} ${targetY}`);
  path.classList.add('connection-line');
  path.setAttribute('data-connection-key', connectionKey);
  path.addEventListener('click', handleConnectionPathClick);
  svg.appendChild(path);
  connections.get(connectionKey).path = path;
}

function removeConnection(connectionKey, path) {
  const connection = connections.get(connectionKey);
  if (!connection) return;

  const nodeId = connectionKey.split('-')[0];
  const universeId = connectionKey.split('-')[1];

  const nodeConnectionCount = nodeConnections.get(nodeId) || 0;
  nodeConnections.set(nodeId, nodeConnectionCount - 1);
  if (nodeConnections.get(nodeId) === 0) nodeConnections.delete(nodeId);
  universeConnections.delete(universeId);

  const nodeLi = document.querySelector(`[data-node-id="${nodeId}"]`);
  const nodeCountSpan = nodeLi.querySelector('[data-type="node-universe-count"]');
  const newCount = nodeConnectionCount - 1;
  nodeCountSpan.textContent = `${newCount} Universe${newCount === 1 ? '' : 's'}`;

  const universeLi = document.querySelector(`[data-universe-id="${universeId}"]`);
  const universeNodeSpan = universeLi.querySelector('[data-type="universe-node"]');
  universeNodeSpan.textContent = 'No Node Patched';

  const universeDiv = universeLi.querySelector('[data-type="cnx_universe"]');
  if (universeDiv) {
    universeDiv.classList.remove('online');
    universeDiv.classList.add('empty');
  }

  const svg = document.getElementById('connection-svg');
  svg.removeChild(path);
  connections.delete(connectionKey);
}

function clearSelection() {
  if (firstSelection) {
    firstSelection.classList.remove('selected');
    firstSelection = null;
  }
  document.querySelectorAll('[data-type="cnx_node"], [data-type="cnx_universe"]').forEach(i => i.classList.remove('selected'));
}

// Node loading
// Node loading
document.addEventListener('DOMContentLoaded', () => {
    updateNodes(true);
    loadFixtures(); // Call loadFixtures here

    // Universe selection
    const universeUl = document.getElementById('universe_ul');
    if (universeUl) {
        universeUl.addEventListener('click', (event) => {
            const listItem = event.target.closest('li.list-item-container.selectable');
            if (!listItem) return;

            // Remove 'chosen' from previously selected item
            const currentChosen = universeUl.querySelector('li.list-item-container.selectable.chosen');
            if (currentChosen) {
                currentChosen.classList.remove('chosen');
            }

            // Add 'chosen' to clicked item
            listItem.classList.add('chosen');

            // Update selectedUniverseId
            selectedUniverseId = listItem.getAttribute('data-universe-id');
            // console.log('Selected Universe ID:', selectedUniverseId); // For debugging
        });
    }

    // Fixture selection
    const fixturesPanel = document.getElementById('fixtures_panel');
    if (fixturesPanel) {
        fixturesPanel.addEventListener('click', (event) => {
            const listItem = event.target.closest('div.list-item-container.selectable');
            if (!listItem) return;

            // Remove 'chosen' from previously selected item
            const currentChosen = fixturesPanel.querySelector('div.list-item-container.selectable.chosen');
            if (currentChosen) {
                currentChosen.classList.remove('chosen');
            }

            // Add 'chosen' to clicked item
            listItem.classList.add('chosen');

            // Update selectedFixtureFile
            selectedFixtureFile = listItem.getAttribute('data-fixture-file');
            // console.log('Selected Fixture File:', selectedFixtureFile); // For debugging
        });
    }

    // Patch button functionality
    const patchButton = document.getElementById('patch-button');
    const patchQtyInput = document.getElementById('patch-qty');
    const startAddressInput = document.getElementById('start-address');

    if (patchButton && patchQtyInput && startAddressInput) {
        patchButton.addEventListener('click', async () => {
            const quantityValue = patchQtyInput.value;
            const startAddressValue = startAddressInput.value;

            if (selectedUniverseId === null) {
                alert("Please select a universe.");
                return;
            }
            if (selectedFixtureFile === null) {
                alert("Please select a fixture.");
                return;
            }

            const quantity = parseInt(quantityValue);
            const startAddress = parseInt(startAddressValue);

            if (isNaN(quantity) || quantity < 1) {
                alert("Please enter a valid quantity (must be a number and at least 1).");
                return;
            }
            if (isNaN(startAddress) || startAddress < 1 || startAddress > 512) { // Assuming DMX addresses 1-512
                alert("Please enter a valid start address (must be a number between 1 and 512).");
                return;
            }

            const payload = {
                fixture_id: selectedFixtureFile, // This is already the filename string
                universe_id: parseInt(selectedUniverseId), // Ensure universe_id is an int
                start_address: startAddress,
                quantity: quantity
            };

            try {
                const response = await fetch('/api/patch', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json(); // Or response.text() if API doesn't return JSON

                if (response.ok) {
                    if (data.message) {
                        alert('Patch successful: ' + data.message);
                    } else {
                        alert('Patch operation completed successfully.'); // Generic success
                    }
                    // Optionally, refresh UI elements or clear selections
                    // e.g., loadUniverses() or clear selections if needed
                } else {
                    if (data.error) {
                        alert('Patch failed: ' + data.error);
                    } else {
                        alert('Patch failed with status: ' + response.status); // More specific error
                    }
                }
            } catch (error) {
                console.error('Error during patch operation:', error);
                alert('Error during patch operation. See console for details.');
            }
        });
    }
});
document.getElementById('refresh-nodes')?.addEventListener('click', () => updateNodes(true));

async function loadFixtures() {
    const fixturesPanel = document.getElementById('fixtures_panel');
    if (!fixturesPanel) {
        console.error('Fixtures panel element not found.');
        return;
    }

    try {
        const response = await fetch('/api/fixtures');
        if (!response.ok) {
            console.error('Failed to fetch fixtures:', response.status, response.statusText);
            fixturesPanel.innerHTML = '<p class="text-red-400">Error loading fixtures.</p>';
            return;
        }

        const fixtures = await response.json();
        
        // Clear existing content
        fixturesPanel.innerHTML = ''; 

        if (fixtures.length === 0) {
            // You can add a placeholder message if no fixtures are available
            // fixturesPanel.innerHTML = '<p class="text-gray-400">No fixtures uploaded yet.</p>';
            // For now, leaving it blank if empty as per original panel behavior
        } else {
            fixtures.forEach(fixture => {
                const fixtureName = fixture.fixture_name || 'Unnamed Fixture';
                const channelCount = fixture.channel_count !== undefined ? fixture.channel_count : 'N/A';
                const iconUrl = '/static/assets/icon_mh.png'; // Direct path for JS
                const fixtureFile = fixture.filename || 'unknown_filename.json';

                const fixtureHTML = `
                    <div class="list-item-container selectable flex flex-col items-center text-center" data-fixture-file="${fixtureFile}">
                        <img alt="Light fixture icon" class="list-item-icon mb-1" src="${iconUrl}" width="160" height="200">
                        <p class="font-medium text-sm">${fixtureName}</p>
                        <p class="text-xs text-gray-400">${channelCount} Channels</p>
                    </div>
                `;
                fixturesPanel.insertAdjacentHTML('beforeend', fixtureHTML);
            });
        }
    } catch (error) {
        console.error('Error fetching or processing fixtures:', error);
        fixturesPanel.innerHTML = '<p class="text-red-400">Error loading fixtures.</p>';
    }
}

// --- Fixture Upload Logic ---
// This DOMContentLoaded listener should be merged with the one above for better practice,
// but for this task, I will keep it separate to strictly follow the instructions of modifying specific parts.
// However, it's better to have a single DOMContentLoaded listener.

document.addEventListener('DOMContentLoaded', () => {
    const fixtureAddButton = document.getElementById('fixture_add');
    const fixtureFileInput = document.getElementById('fixture_file_input');

    if (fixtureAddButton) {
        fixtureAddButton.addEventListener('click', () => {
            if (fixtureFileInput) {
                fixtureFileInput.click();
            }
        });
    }

    if (fixtureFileInput) {
        fixtureFileInput.addEventListener('change', async (event) => {
            const file = event.target.files[0];
            if (!file) {
                return; // No file selected
            }

            if (file.type !== 'application/json') {
                alert('Please select a valid JSON file.');
                // Reset file input
                fixtureFileInput.value = '';
                return;
            }

            const formData = new FormData();
            formData.append('file', file); // 'file' is the name the server will expect

            try {
                const response = await fetch('/api/fixtures/upload', {
                    method: 'POST',
                    body: formData,
                });

                const result = await response.json();

                if (response.ok) {
                    alert(result.message || 'Fixture uploaded successfully!');
                    // Later, we will call a function here to refresh the fixtures list,
                    // for example: loadFixtures();
                    if (typeof loadFixtures === 'function') {
                        loadFixtures();
                    } else {
                        console.warn('loadFixtures function not yet defined. Fixture list may not auto-refresh.');
                    }
                } else {
                    alert(result.error || 'Error uploading fixture.');
                }
            } catch (error) {
                console.error('Error during fixture upload:', error);
                alert('An unexpected error occurred during upload.');
            } finally {
                // Reset file input so the same file can be selected again if needed
                fixtureFileInput.value = '';
            }
        });
    }
});