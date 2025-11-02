/**
 * Profile page functionality
 */

let isEditing = false;

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    loadProfile();
});

// Load profile data
async function loadProfile() {
    try {
        const response = await window.api.getProfile();
        
        if (response.status === 'success' && response.data) {
            renderProfile(response.data);
        } else {
            // Try to get from localStorage
            const user = window.utils.getUser();
            if (user) {
                renderProfile(user);
            }
        }
    } catch (error) {
        console.error('Error loading profile:', error);
        // Use cached user data
        const user = window.utils.getUser();
        if (user) {
            renderProfile(user);
        } else {
            showAlert('error', 'Failed to load profile');
        }
    }
}

// Render profile
function renderProfile(user) {
    document.getElementById('profile-loading').style.display = 'none';
    document.getElementById('profile-content').style.display = 'block';
    
    // Header
    const name = user.first_name && user.last_name 
        ? `${user.first_name} ${user.last_name}`
        : user.username || user.email;
    document.getElementById('profile-name').textContent = name;
    document.getElementById('profile-email').textContent = user.email;
    document.getElementById('token-balance').textContent = user.token_balance || 0;
    
    // Avatar
    const avatar = document.getElementById('profile-avatar');
    if (user.avatar_url) {
        avatar.innerHTML = `<img src="${user.avatar_url}" alt="Avatar" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`;
    } else {
        const initials = name.split(' ').map(n => n[0]).join('').toUpperCase().substring(0, 2);
        avatar.textContent = initials || '👤';
    }
    
    // Personal Info
    document.getElementById('info-email').textContent = user.email;
    document.getElementById('info-username').textContent = user.username;
    document.getElementById('display-first-name').textContent = user.first_name || 'Not set';
    document.getElementById('display-last-name').textContent = user.last_name || 'Not set';
    document.getElementById('edit-first-name').value = user.first_name || '';
    document.getElementById('edit-last-name').value = user.last_name || '';
    
    const educationLabels = {
        'high_school': 'High School',
        'bachelor': 'Bachelor',
        'master': 'Master',
        'phd': 'PhD'
    };
    document.getElementById('display-education').textContent = educationLabels[user.education_level] || 'Not specified';
    document.getElementById('edit-education').value = user.education_level || '';
    
    // Settings
    document.getElementById('email-verified-status').innerHTML = user.is_verified 
        ? '<span style="color: var(--success);">✓ Verified</span>' 
        : '<span style="color: var(--warning);">✗ Not Verified</span>';
    document.getElementById('wallet-address').textContent = user.wallet_address || 'Not connected';
    document.getElementById('account-status').innerHTML = user.is_active 
        ? '<span style="color: var(--success);">Active</span>' 
        : '<span style="color: var(--error);">Inactive</span>';
}

// Switch tab
function switchTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`tab-${tabName}`).classList.add('active');
    event.target.classList.add('active');
}

// Toggle edit mode
function toggleEditInfo() {
    isEditing = !isEditing;
    const editBtn = document.getElementById('edit-info-btn');
    const saveButtons = document.getElementById('save-info-buttons');
    
    if (isEditing) {
        editBtn.textContent = 'Cancel';
        saveButtons.style.display = 'block';
        document.getElementById('edit-first-name').style.display = 'block';
        document.getElementById('display-first-name').style.display = 'none';
        document.getElementById('edit-last-name').style.display = 'block';
        document.getElementById('display-last-name').style.display = 'none';
        document.getElementById('edit-education').style.display = 'block';
        document.getElementById('display-education').style.display = 'none';
    } else {
        cancelEditInfo();
    }
}

// Cancel edit
function cancelEditInfo() {
    isEditing = false;
    const editBtn = document.getElementById('edit-info-btn');
    const saveButtons = document.getElementById('save-info-buttons');
    
    editBtn.textContent = 'Edit';
    saveButtons.style.display = 'none';
    document.getElementById('edit-first-name').style.display = 'none';
    document.getElementById('display-first-name').style.display = 'inline';
    document.getElementById('edit-last-name').style.display = 'none';
    document.getElementById('display-last-name').style.display = 'inline';
    document.getElementById('edit-education').style.display = 'none';
    document.getElementById('display-education').style.display = 'inline';
    
    // Reset values
    loadProfile();
}

// Handle profile update
async function handleUpdateProfile(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = {
        first_name: document.getElementById('edit-first-name').value.trim(),
        last_name: document.getElementById('edit-last-name').value.trim(),
        education_level: document.getElementById('edit-education').value
    };
    
    const submitBtn = form.querySelector('button[type="submit"]');
    window.utils.setLoading(submitBtn, true);
    
    try {
        const response = await window.api.updateProfile(formData);
        
        if (response.status === 'success') {
            showAlert('success', 'Profile updated successfully!');
            cancelEditInfo();
            loadProfile();
        }
    } catch (error) {
        showAlert('error', error.message || 'Failed to update profile');
    } finally {
        window.utils.setLoading(submitBtn, false);
    }
}

// Handle password change
async function handleChangePassword(event) {
    event.preventDefault();
    
    const form = event.target;
    const oldPassword = form.old_password.value;
    const newPassword = form.new_password.value;
    const confirmPassword = form.confirm_password.value;
    
    if (newPassword !== confirmPassword) {
        showAlert('error', 'New passwords do not match');
        return;
    }
    
    if (!window.utils.validatePassword(newPassword)) {
        showAlert('error', 'Password must be at least 8 characters');
        return;
    }
    
    const submitBtn = form.querySelector('button[type="submit"]');
    window.utils.setLoading(submitBtn, true);
    
    try {
        const response = await window.api.changePassword(oldPassword, newPassword);
        
        if (response.status === 'success') {
            showAlert('success', 'Password changed successfully!');
            form.reset();
        }
    } catch (error) {
        showAlert('error', error.message || 'Failed to change password');
    } finally {
        window.utils.setLoading(submitBtn, false);
    }
}

// Show alert - use centralized utility
function showAlert(type, message) {
    if (window.utils && window.utils.showAlert) {
        window.utils.showAlert(type, message);
    }
}

// Load wallet data
async function loadWalletData() {
    try {
        const profileResponse = await window.api.getProfile();
        const user = profileResponse.data || window.utils.getUser();
        
        if (user && user.wallet_address) {
            document.getElementById('wallet-connected').style.display = 'block';
            document.getElementById('wallet-disconnected').style.display = 'none';
            document.getElementById('wallet-address').textContent = user.wallet_address;
            
            // Load wallet balance
            try {
                const balanceResponse = await window.api.getWalletBalance();
                if (balanceResponse.data && balanceResponse.data.balance) {
                    document.getElementById('wallet-balance').textContent = `${balanceResponse.data.balance} ${balanceResponse.data.symbol || 'ETH'}`;
                } else {
                    document.getElementById('wallet-balance').textContent = 'N/A';
                }
            } catch (e) {
                document.getElementById('wallet-balance').textContent = 'N/A';
            }
            
            // Get network from wallet connection if available
            if (user.wallet_connection && user.wallet_connection.network) {
                document.getElementById('wallet-network').textContent = user.wallet_connection.network.toUpperCase();
            } else {
                document.getElementById('wallet-network').textContent = 'Unknown';
            }
        } else {
            document.getElementById('wallet-connected').style.display = 'none';
            document.getElementById('wallet-disconnected').style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading wallet data:', error);
    }
}

// Load blockchain stats
async function loadBlockchainStats() {
    try {
        const response = await window.api.getBlockchainStats();
        // Handle response format - can be direct data or wrapped
        const data = response.data || response;
        if (data) {
            document.getElementById('stat-payments').textContent = data.total_on_chain_payments || 0;
            document.getElementById('stat-tokens').textContent = data.total_tokens_transferred || 0;
            document.getElementById('stat-certificates').textContent = data.certificates_minted || 0;
        }
    } catch (error) {
        console.error('Error loading blockchain stats:', error);
        // Set defaults on error
        document.getElementById('stat-payments').textContent = '0';
        document.getElementById('stat-tokens').textContent = '0';
        document.getElementById('stat-certificates').textContent = '0';
    }
}

// Load certificates
async function loadCertificates() {
    const container = document.getElementById('certificates-list');
    if (!container) return;
    
    try {
        const response = await window.api.getCertificates();
        if (response.status === 'success' && response.data && response.data.length > 0) {
            container.innerHTML = response.data.map(cert => `
                <div style="padding: var(--spacing-md); background: var(--bg-secondary); border-radius: var(--border-radius); border: 1px solid var(--border-color);">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: var(--spacing-sm);">
                        <div>
                            <h3 style="margin: 0 0 var(--spacing-xs) 0;">${cert.course_name || 'Course Certificate'}</h3>
                            <p style="color: var(--text-secondary); margin: 0; font-size: 0.9rem;">
                                Completed: ${new Date(cert.completion_date).toLocaleDateString()}
                            </p>
                        </div>
                        <span style="padding: var(--spacing-xs) var(--spacing-sm); background: var(--accent-primary); color: white; border-radius: var(--border-radius); font-size: 0.8rem; font-weight: 600;">
                            ${cert.status === 'minted' ? '✓ Minted' : cert.status}
                        </span>
                    </div>
                    ${cert.nft_token_id ? `
                        <div style="margin-top: var(--spacing-sm); padding-top: var(--spacing-sm); border-top: 1px solid var(--border-color);">
                            <div style="font-size: 0.85rem; color: var(--text-secondary);">
                                <strong>NFT Token ID:</strong> ${cert.nft_token_id}<br>
                                ${cert.nft_contract_address ? `<strong>Contract:</strong> ${cert.nft_contract_address.substring(0, 20)}...` : ''}
                            </div>
                        </div>
                    ` : ''}
                    ${cert.status !== 'minted' ? `
                        <button class="btn btn-secondary" onclick="verifyCertificate(${cert.id})" style="margin-top: var(--spacing-sm); font-size: 0.9rem;">
                            Verify Certificate
                        </button>
                    ` : ''}
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: var(--spacing-xl);">No certificates yet. Complete courses to earn certificates!</p>';
        }
    } catch (error) {
        console.error('Error loading certificates:', error);
        container.innerHTML = '<p style="color: var(--text-error); text-align: center; padding: var(--spacing-xl);">Failed to load certificates</p>';
    }
}

// Connect wallet - updated to use MetaMask
async function connectWallet() {
    // Check if MetaMask is available
    if (typeof window.ethereum === 'undefined') {
        // Show user-friendly message
        const installMetaMask = confirm(
            'MetaMask is not installed.\n\n' +
            'To connect your wallet, you need to install MetaMask:\n' +
            '1. Visit https://metamask.io/\n' +
            '2. Install the browser extension\n' +
            '3. Create or import a wallet\n' +
            '4. Then come back and try again\n\n' +
            'Would you like to enter a wallet address manually instead?'
        );
        
        if (installMetaMask) {
            // Allow manual wallet address entry
            const walletAddress = prompt('Enter your wallet address (0x...):');
            if (!walletAddress) return;
            
            // Basic validation
            if (!walletAddress.startsWith('0x') || walletAddress.length !== 42) {
                showAlert('error', 'Invalid wallet address format. Must start with 0x and be 42 characters.');
                return;
            }
            
            // Use a dummy signature for manual entry (backend should handle this)
            try {
                const response = await window.api.connectWallet({
                    wallet_address: walletAddress,
                    signature: 'manual_entry',
                    network: 'sepolia'
                });
                if (response.status === 'success') {
                    showAlert('success', 'Wallet connected successfully!');
                    const user = window.utils.getUser();
                    if (user) {
                        user.wallet_address = walletAddress;
                        window.utils.setUser(user);
                    }
                    loadWalletData();
                    loadBlockchainStats();
                }
            } catch (error) {
                showAlert('error', error.message || 'Failed to connect wallet');
            }
        }
        return;
    }
    
    try {
        // Show connecting message
        showAlert('info', 'Requesting MetaMask connection...');
        
        // Request account access - this will prompt the user
        const accounts = await window.ethereum.request({ 
            method: 'eth_requestAccounts' 
        });
        
        if (!accounts || accounts.length === 0) {
            showAlert('error', 'No accounts found. Please unlock MetaMask and try again.');
            return;
        }
        
        const walletAddress = accounts[0];
        
        // Check if already connected to correct network
        const chainId = await window.ethereum.request({ method: 'eth_chainId' });
        const sepoliaChainId = '0xaa36a7'; // Sepolia testnet
        
        if (chainId !== sepoliaChainId) {
            try {
                // Request to switch to Sepolia
                await window.ethereum.request({
                    method: 'wallet_switchEthereumChain',
                    params: [{ chainId: sepoliaChainId }],
                });
            } catch (switchError) {
                // If network doesn't exist, add it
                if (switchError.code === 4902) {
                    await window.ethereum.request({
                        method: 'wallet_addEthereumChain',
                        params: [{
                            chainId: sepoliaChainId,
                            chainName: 'Sepolia Test Network',
                            nativeCurrency: {
                                name: 'ETH',
                                symbol: 'ETH',
                                decimals: 18
                            },
                            rpcUrls: ['https://sepolia.infura.io/v3/'],
                            blockExplorerUrls: ['https://sepolia.etherscan.io']
                        }]
                    });
                } else {
                    throw switchError;
                }
            }
        }
        
        // Create a message to sign
        const message = `Connect to Blockchain AI LMS\n\nWallet: ${walletAddress}\nTimestamp: ${new Date().toISOString()}`;
        
        // Request signature - this will show MetaMask popup
        showAlert('info', 'Please sign the message in MetaMask to verify your wallet...');
        
        const signature = await window.ethereum.request({
            method: 'personal_sign',
            params: [message, walletAddress]
        });
        
        if (!signature) {
            showAlert('error', 'Signature was cancelled');
            return;
        }
        
        // Connect to backend - send as object
        const response = await window.api.connectWallet({
            wallet_address: walletAddress,
            signature: signature,
            network: 'sepolia'
        });
        
        if (response.status === 'success') {
            showAlert('success', 'Wallet connected successfully!');
            // Update user profile with wallet address
            const user = window.utils.getUser();
            if (user) {
                user.wallet_address = walletAddress;
                window.utils.setUser(user);
            }
            loadWalletData();
            loadBlockchainStats();
        } else {
            showAlert('error', response.message || 'Failed to connect wallet');
        }
    } catch (error) {
        console.error('Wallet connection error:', error);
        if (error.code === 4001) {
            showAlert('error', 'Wallet connection was rejected. Please try again and approve the request.');
        } else if (error.code === -32002) {
            showAlert('error', 'Connection request already pending. Please check MetaMask.');
        } else {
            showAlert('error', error.message || 'Failed to connect wallet. Please try again.');
        }
    }
}

// Disconnect wallet
async function disconnectWallet() {
    if (!confirm('Are you sure you want to disconnect your wallet?')) {
        return;
    }
    
    try {
        await window.api.disconnectWallet();
        showAlert('success', 'Wallet disconnected');
        loadWalletData();
    } catch (error) {
        showAlert('error', error.message || 'Failed to disconnect wallet');
    }
}

// Verify certificate
async function verifyCertificate(certId) {
    try {
        const response = await window.api.verifyCertificate(certId);
        if (response.status === 'success') {
            showAlert('success', 'Certificate verification initiated');
            loadCertificates();
        }
    } catch (error) {
        showAlert('error', error.message || 'Failed to verify certificate');
    }
}

// Load preferences
async function loadPreferences() {
    try {
        const response = await window.api.getPreferences();
        if (response.status === 'success' && response.data) {
            const prefs = response.data;
            
            document.getElementById('pref-categories').textContent = 
                prefs.preferred_categories && prefs.preferred_categories.length > 0
                    ? prefs.preferred_categories.join(', ')
                    : 'Not set';
            document.getElementById('pref-difficulty').textContent = 
                prefs.preferred_difficulty || 'Any';
            document.getElementById('pref-learning-style').textContent = 
                prefs.learning_style ? prefs.learning_style.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Video';
            // Note: learning_goals not in model yet, showing placeholder
            document.getElementById('pref-goals').textContent = 'Feature coming soon';
            
            // Populate form if editing
            const form = document.getElementById('preferences-form');
            if (form) {
                // Set checkboxes
                form.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                    cb.checked = prefs.preferred_categories && prefs.preferred_categories.includes(cb.value);
                });
                
                // Set selects
                if (form.querySelector('[name="difficulty"]')) {
                    form.querySelector('[name="difficulty"]').value = prefs.preferred_difficulty || '';
                }
                if (form.querySelector('[name="learning_style"]')) {
                    form.querySelector('[name="learning_style"]').value = prefs.learning_style || 'video';
                }
            }
        }
    } catch (error) {
        console.error('Error loading preferences:', error);
        // Set defaults
        document.getElementById('pref-categories').textContent = 'Not set';
        document.getElementById('pref-difficulty').textContent = 'Any';
        document.getElementById('pref-learning-style').textContent = 'Video';
        document.getElementById('pref-goals').textContent = 'Feature coming soon';
    }
}

// Toggle edit preferences
function toggleEditPreferences() {
    const form = document.getElementById('preferences-form');
    const display = document.getElementById('preferences-display');
    const editBtn = document.getElementById('edit-preferences-btn');
    
    if (form && display) {
        form.style.display = 'block';
        display.style.display = 'none';
        editBtn.style.display = 'none';
    }
}

// Cancel edit preferences
function cancelEditPreferences() {
    const form = document.getElementById('preferences-form');
    const display = document.getElementById('preferences-display');
    const editBtn = document.getElementById('edit-preferences-btn');
    
    if (form && display) {
        form.style.display = 'none';
        display.style.display = 'block';
        editBtn.style.display = 'block';
        loadPreferences(); // Reload to reset form
    }
}

// Update preferences
async function handleUpdatePreferences(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    
    const categories = [];
    form.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
        categories.push(cb.value);
    });
    
    const preferences = {
        preferred_categories: categories,
        preferred_difficulty: formData.get('difficulty') || null,
        learning_style: formData.get('learning_style') || 'video'
        // Note: learning_goals not in model yet - can be added later
    };
    
    const submitBtn = form.querySelector('button[type="submit"]');
    window.utils.setLoading(submitBtn, true);
    
    try {
        const response = await window.api.updatePreferences(preferences);
        if (response.status === 'success') {
            showAlert('success', 'Preferences updated successfully!');
            cancelEditPreferences();
            loadPreferences();
        }
    } catch (error) {
        showAlert('error', error.message || 'Failed to update preferences');
    } finally {
        window.utils.setLoading(submitBtn, false);
    }
}

// Update switchTab to load data when switching to wallet/certificates/preferences tabs
const originalSwitchTab = switchTab;
switchTab = function(tabName) {
    originalSwitchTab(tabName);
    
    if (tabName === 'wallet') {
        loadWalletData();
        loadBlockchainStats();
    } else if (tabName === 'certificates') {
        loadCertificates();
    } else if (tabName === 'preferences') {
        loadPreferences();
    }
};

// Make functions available globally
window.switchTab = switchTab;
window.toggleEditInfo = toggleEditInfo;
window.cancelEditInfo = cancelEditInfo;
window.connectWallet = connectWallet;
window.disconnectWallet = disconnectWallet;
window.verifyCertificate = verifyCertificate;
window.toggleEditPreferences = toggleEditPreferences;
window.cancelEditPreferences = cancelEditPreferences;
window.handleUpdatePreferences = handleUpdatePreferences;

