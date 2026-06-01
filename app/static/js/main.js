// ReelWrapped JavaScript



document.addEventListener('DOMContentLoaded', function() {
    // Tab functionality
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.textContent.toLowerCase().replace(' ', '-');
            showTab(tabName);
        });
    });

    // Search functionality
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', filterContent);
    }

    // Filter functionality
    const filterSelect = document.getElementById('filter-select');
    if (filterSelect) {
        filterSelect.addEventListener('change', filterContent);
    }

    // Sort functionality
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            const sortValue = this.value;
            // Update URL with sort parameter
            const url = new URL(window.location);
            url.searchParams.set('sort', sortValue);
            window.location.href = url.toString();
        });
    }

    // Follow/Unfollow buttons
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('follow-btn') || e.target.classList.contains('unfollow-btn')) {
            handleFollow(e.target);
        }
    });

    // User link clicks on mutuals page
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('user-link')) {
            const userId = e.target.dataset.userId;
            if (userId) {
                window.location.href = `/user/${userId}`;
            }
        }
    });

    // Modal functionality
    const editBtn = document.querySelector('.profile-info .btn');
    if (editBtn && editBtn.textContent.includes('Edit')) {
        editBtn.addEventListener('click', showEditModal);
    }

    // File upload validation
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', validateFile);
    });

    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', validateForm);
    });

    // Hashtag button functionality
    const hashtagButtons = document.querySelectorAll('.hashtag-btn');
    hashtagButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            this.classList.toggle('selected');
        });
    });

    // Initialize selected hashtags from user data
    initializeSelectedHashtags();
});

function showTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));

    // Remove active class from all buttons
    const buttons = document.querySelectorAll('.tab-btn');
    buttons.forEach(btn => btn.classList.remove('active'));

    // Show selected tab
    const selectedTab = document.getElementById(tabName + '-tab');
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Add active class to clicked button
    event.target.classList.add('active');

    // Load reposts if reposts tab is selected
    if (tabName === 'reposts') {
        loadReposts();
    }
}

function loadReposts() {
    const repostsContainer = document.getElementById('reposts-container');
    if (!repostsContainer) return;

    // Show loading state
    repostsContainer.innerHTML = '<div class="loading">Loading reposts...</div>';

    // Get current user ID
    const userId = getCurrentUserId();

    // Fetch reposts
    fetch(`/api/reposts/${userId}`)
        .then(response => response.json())
        .then(data => {
            repostsContainer.innerHTML = '';
            
            if (data.length === 0) {
                repostsContainer.innerHTML = '<p style="color: white; text-align: center; padding: 40px;">No reposts yet. Visit the home page to repost trends!</p>';
            } else {
                data.forEach(repost => {
                    const repostCard = createRepostCard(repost);
                    repostsContainer.appendChild(repostCard);
                });
            }
        })
        .catch(error => {
            console.error('Error loading reposts:', error);
            repostsContainer.innerHTML = '<p style="color: white; text-align: center;">Error loading reposts.</p>';
        });
}

function createRepostCard(repost) {
    const card = document.createElement('div');
    card.className = 'repost-card';
    
    let icon, linkUrl, username, displayName, countLabel;
    
    // Determine content based on repost type
    if (repost.trend_type === 'hashtag') {
        icon = '#';
        username = repost.trend_name;
        displayName = repost.trend_name;
        countLabel = 'posts';
        linkUrl = `/hashtag/${repost.trend_name.substring(1)}`;
    } else if (repost.trend_type === 'music') {
        icon = '♪';
        username = repost.trend_name;
        displayName = repost.trend_name;
        countLabel = 'likes';
        linkUrl = `/music/${encodeURIComponent(repost.trend_name)}`;
    } else if (repost.trend_type === 'creator') {
        icon = '★';
        username = repost.trend_name;
        displayName = repost.trend_name;
        countLabel = 'followers';
        linkUrl = `/creator/${repost.trend_name.substring(1)}`;
    }
    
    // Format the date
    const repostDate = new Date(repost.created_at);
    const formattedDate = repostDate.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit' 
    }).replace(/\//g, '/');
    
    // Create the card HTML with the new design
    card.innerHTML = `
        <div class="repost-card-content">
            <div class="repost-card-header">
                <div class="repost-card-icon">${icon}</div>
                <div class="repost-card-user">
                    <h3 class="repost-card-username">${displayName}</h3>
                    <p class="repost-card-followers">${repost.count.toLocaleString()} ${countLabel}</p>
                </div>
            </div>
            <div class="repost-card-body">
                <h4 class="repost-card-title">${repost.trend_type === 'music' ? '♪ ' : ''}${displayName}</h4>
                <p class="repost-card-meta">${repost.count.toLocaleString()} ${countLabel}</p>
            </div>
            <div class="repost-card-footer">
                <span class="repost-card-date">Reposted ${formattedDate}</span>
                <button class="unrepost-btn" onclick="event.preventDefault(); unrepostTrend(${repost.trend_id}, this)">
                    <span>Remove</span>
                </button>
            </div>
        </div>
    `;
    
    // Make the entire card clickable
    card.addEventListener('click', (e) => {
        // Don't navigate if the click was on the remove button
        if (!e.target.closest('.unrepost-btn')) {
            window.location.href = linkUrl;
        }
    });
    
    return card;
}

function unrepostTrend(trendId) {
    if (!confirm('Remove this repost?')) return;
    
    fetch(`/unrepost/${trendId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload reposts
            loadReposts();
            showAlert('Repost removed successfully', 'success');
        } else {
            showAlert(data.message || 'Failed to remove repost', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while removing repost', 'error');
    });
}

function filterContent() {
    const searchTerm = document.getElementById('search-input')?.value.toLowerCase() || '';
    const filterValue = document.getElementById('filter-select')?.value || 'all';

    // Handle trend cards on home page
    const trendCards = document.querySelectorAll('.trend-card');
    if (trendCards.length > 0) {
        trendCards.forEach(card => {
            const name = card.dataset.name?.toLowerCase() || '';
            const type = card.dataset.type || '';

            const matchesSearch = name.includes(searchTerm);
            const matchesFilter = filterValue === 'all' || type === filterValue;

            if (matchesSearch && matchesFilter) {
                card.closest('.trend-card-link').style.display = 'block';
            } else {
                card.closest('.trend-card-link').style.display = 'none';
            }
        });
    }

    // Handle user cards on mutuals page
    const userCards = document.querySelectorAll('.user-card');
    if (userCards.length > 0) {
        userCards.forEach(card => {
            const name = card.querySelector('h3')?.textContent.toLowerCase() || '';

            const matchesSearch = name.includes(searchTerm);

            if (matchesSearch) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }
}

function sortContent() {
    const sortValue = document.getElementById('sort-select')?.value || 'popular';

    // Handle trend cards on home page
    const trendContainers = document.querySelectorAll('.cards-container');
    if (trendContainers.length > 0) {
        trendContainers.forEach(container => {
            const cards = Array.from(container.children);

            cards.sort((a, b) => {
                if (sortValue === 'alphabetical') {
                    const nameA = a.querySelector('h3')?.textContent || '';
                    const nameB = b.querySelector('h3')?.textContent || '';
                    return nameA.localeCompare(nameB);
                } else if (sortValue === 'recent') {
                    const dateA = new Date(a.querySelector('.trend-card')?.dataset.lastUpdated || 0);
                    const dateB = new Date(b.querySelector('.trend-card')?.dataset.lastUpdated || 0);
                    return dateB - dateA;
                } else {
                    // Popular (default) - sort by count
                    const countA = parseInt(a.querySelector('.trend-card')?.dataset.count || 0);
                    const countB = parseInt(b.querySelector('.trend-card')?.dataset.count || 0);
                    return countB - countA;
                }
            });

            cards.forEach(card => container.appendChild(card));
        });
    }

    // Handle user cards on mutuals page
    const userContainer = document.getElementById('mutuals-container');
    if (userContainer) {
        const cards = Array.from(userContainer.children);

        cards.sort((a, b) => {
            if (sortValue === 'alphabetical') {
                const nameA = a.querySelector('h3')?.textContent || '';
                const nameB = b.querySelector('h3')?.textContent || '';
                return nameA.localeCompare(nameB);
            } else if (sortValue === 'followers') {
                const followersA = parseInt(a.querySelector('.stat')?.textContent.match(/\d+/) || 0);
                const followersB = parseInt(b.querySelector('.stat')?.textContent.match(/\d+/) || 0);
                return followersB - followersA;
            } else {
                // Match (default) - sort by match percentage
                const matchA = parseInt(a.querySelector('.match-score')?.textContent.match(/\d+/) || 0);
                const matchB = parseInt(b.querySelector('.match-score')?.textContent.match(/\d+/) || 0);
                return matchB - matchA;
            }
        });

        cards.forEach(card => userContainer.appendChild(card));
    }
}

async function handleFollow(button) {
    const userId = button.dataset.userId;
    const hashtagName = button.dataset.hashtagName;
    const songName = button.dataset.songName;
    let isFollowing = button.dataset.following === 'true';
    let action, url;

    if (userId) {
        // User follow/unfollow
        action = isFollowing ? 'unfollow' : 'follow';
        url = `/mutuals/${action}/${userId}`;
    } else if (hashtagName) {
        // Hashtag follow/unfollow
        action = isFollowing ? 'unfollow' : 'follow';
        url = `/hashtag/${action}/${hashtagName}`;
    } else if (songName) {
        // Music follow/unfollow
        action = isFollowing ? 'unfollow' : 'follow';
        url = `/music/${action}/${encodeURIComponent(songName)}`;
    } else if (button.dataset.creatorName) {
        // Creator follow/unfollow
        const creatorName = button.dataset.creatorName;
        action = isFollowing ? 'unfollow' : 'follow';
        url = `/creator/${action}/${creatorName}`;
    } else {
        showAlert('Invalid follow action', 'error');
        return;
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json();

        if (data.success) {
            if (isFollowing) {
                button.textContent = 'Follow';
                button.classList.remove('btn-secondary');
                button.classList.add('btn-primary');
                button.dataset.following = 'false';
                button.classList.remove('unfollow-btn');
                button.classList.add('follow-btn');
            } else {
                button.textContent = 'Unfollow';
                button.classList.remove('btn-primary');
                button.classList.add('btn-secondary');
                button.dataset.following = 'true';
                button.classList.remove('follow-btn');
                button.classList.add('unfollow-btn');
            }
            showAlert(data.message, 'success');
        } else {
            showAlert(data.message, 'error');
        }
    } catch (error) {
        showAlert('An error occurred', 'error');
    }
}

function showEditModal() {
    const modal = document.getElementById('edit-modal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeEditModal() {
    const modal = document.getElementById('edit-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function submitEditForm() {
    const form = document.getElementById('edit-form');
    const formData = new FormData(form);

    // Add bio field to form data
    const bioTextarea = document.getElementById('edit-bio');
    if (bioTextarea) {
        formData.append('bio', bioTextarea.value);
    }

    // Add selected hashtags to form data
    const selectedHashtags = [];
    const hashtagButtons = document.querySelectorAll('.hashtag-btn.selected');
    hashtagButtons.forEach(btn => {
        selectedHashtags.push(btn.dataset.hashtag);
    });
    formData.append('hashtags', selectedHashtags.join(','));

    fetch('/profile', {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(data => {
        // Reload the page to show updated profile
        window.location.reload();
    })
    .catch(error => {
        console.error('Error:', error);
        showAlert('An error occurred while updating profile', 'error');
    });

    return false; // Prevent default form submission
}

function validateFile(event) {
    const file = event.target.files[0];
    const inputName = event.target.name;

    if (file) {
        if (inputName === 'profile_image') {
            // Validate profile image files
            const allowedExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp'];
            const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));

            if (!allowedExtensions.includes(fileExtension)) {
                showAlert('Only image files (JPG, PNG, GIF, WebP) are allowed for profile pictures', 'error');
                event.target.value = '';
            } else if (file.size > 5 * 1024 * 1024) { // 5MB for images
                showAlert('Image file size must be less than 5MB', 'error');
                event.target.value = '';
            } else {
                showAlert('Profile image selected successfully', 'success');
            }
        } else if (inputName === 'activity_log') {
            // Validate activity log files (ZIP only)
            if (!file.name.toLowerCase().endsWith('.zip')) {
                showAlert('Only .zip files are allowed for activity logs', 'error');
                event.target.value = '';
            } else if (file.size > 16 * 1024 * 1024) { // 16MB
                showAlert('File size must be less than 16MB', 'error');
                event.target.value = '';
            } else {
                showAlert('Activity log selected successfully', 'success');
            }
        }
    }
}

function validateForm(event) {
    const form = event.target;
    const requiredFields = form.querySelectorAll('input[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.style.borderColor = '#dc3545';
            isValid = false;
        } else {
            field.style.borderColor = '#ddd';
        }
    });

    // Email validation
    const emailField = form.querySelector('input[type="email"]');
    if (emailField && emailField.value) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(emailField.value)) {
            emailField.style.borderColor = '#dc3545';
            isValid = false;
        }
    }

    // Password confirmation
    const password = form.querySelector('input[name="password"]');
    const confirmPassword = form.querySelector('input[name="confirm_password"]');
    if (password && confirmPassword && password.value !== confirmPassword.value) {
        confirmPassword.style.borderColor = '#dc3545';
        isValid = false;
    }

    if (!isValid) {
        event.preventDefault();
        showAlert('Please fill in all required fields correctly', 'error');
    }
}

function showAlert(message, type) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;

    const container = document.querySelector('.container') || document.body;
    container.insertBefore(alertDiv, container.firstChild);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('edit-modal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

function closeUploadModal() {
    const modal = document.getElementById('upload-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function initializeSelectedHashtags() {
    // Get user's current hashtags from the profile display
    const profileHashtags = document.querySelectorAll('.profile-hashtags .hashtag-tag');
    const userHashtags = Array.from(profileHashtags).map(tag => tag.textContent.trim());

    // Select the corresponding buttons in the edit modal
    const hashtagButtons = document.querySelectorAll('.hashtag-btn');
    hashtagButtons.forEach(btn => {
        const hashtag = btn.dataset.hashtag;
        if (userHashtags.includes(hashtag)) {
            btn.classList.add('selected');
        }
    });
}

// Followers and Following Modal Functions
function showFollowersModal() {
    const modal = document.getElementById('followers-modal');
    const list = document.getElementById('followers-list');

    if (modal && list) {
        // Clear previous content
        list.innerHTML = '<div class="loading">Loading...</div>';

        // Fetch followers data
        fetch('/api/followers/' + getCurrentUserId())
            .then(response => response.json())
            .then(data => {
                list.innerHTML = '';
                if (data.length === 0) {
                    list.innerHTML = '<p>No followers yet.</p>';
                } else {
                    data.forEach(user => {
                        const userItem = createUserListItem(user);
                        list.appendChild(userItem);
                    });
                }
            })
            .catch(error => {
                console.error('Error loading followers:', error);
                list.innerHTML = '<p>Error loading followers.</p>';
            });

        modal.style.display = 'block';
    }
}

function showFollowingModal() {
    const modal = document.getElementById('following-modal');
    const list = document.getElementById('following-list');

    if (modal && list) {
        // Clear previous content
        list.innerHTML = '<div class="loading">Loading...</div>';

        // Fetch following data
        fetch('/api/following/' + getCurrentUserId())
            .then(response => response.json())
            .then(data => {
                list.innerHTML = '';
                if (data.length === 0) {
                    list.innerHTML = '<p>Not following anyone yet.</p>';
                } else {
                    data.forEach(user => {
                        const userItem = createUserListItem(user);
                        list.appendChild(userItem);
                    });
                }
            })
            .catch(error => {
                console.error('Error loading following:', error);
                list.innerHTML = '<p>Error loading following.</p>';
            });

        modal.style.display = 'block';
    }
}

function closeFollowersModal() {
    const modal = document.getElementById('followers-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function closeFollowingModal() {
    const modal = document.getElementById('following-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function createUserListItem(user) {
    const item = document.createElement('div');
    item.className = 'user-list-item';

    if (user.type === 'hashtag') {
        item.innerHTML = `
            <div class="hashtag-list-icon">
                <span class="hashtag-symbol">#</span>
            </div>
            <div class="user-list-info">
                <h4><a href="/hashtag/${user.username}" style="text-decoration: none; color: inherit;">#${user.username}</a></h4>
                <p>Hashtag</p>
            </div>
        `;
    } else if (user.type === 'music') {
        item.innerHTML = `
            <div class="music-list-icon">
                <span class="music-symbol">♪</span>
            </div>
            <div class="user-list-info">
                <h4><a href="/music/${encodeURIComponent(user.username)}" style="text-decoration: none; color: inherit;">${user.username}</a></h4>
                <p>Music</p>
            </div>
        `;
    } else if (user.type === 'creator') {
        item.innerHTML = `
            <div class="creator-list-icon">
                <span class="creator-symbol">★</span>
            </div>
            <div class="user-list-info">
                <h4><a href="/creator/${user.username}" style="text-decoration: none; color: inherit;">${user.username}</a></h4>
                <p>Creator</p>
            </div>
        `;
    } else {
        item.innerHTML = `
            <img src="${user.profile_image_url}" alt="${user.username}" class="user-list-avatar">
            <div class="user-list-info">
                <h4><a href="/user/${user.id}" style="text-decoration: none; color: inherit;">${user.username}</a></h4>
                <p>Click to view profile</p>
            </div>
        `;
    }

    return item;
}

function getCurrentUserId() {
    // Extract user ID from a hidden element or global variable
    // Look for a data attribute on the body or a global variable set by the server
    const userIdElement = document.querySelector('[data-current-user-id]');
    if (userIdElement) {
        return userIdElement.dataset.currentUserId;
    }
    // Fallback: assume it's the current user's profile
    return 'current';
}

// Trend Users Modal Functions
function showTrendUsersModal(trendType, trendName) {
    const modal = document.getElementById('trend-users-modal');
    const list = document.getElementById('trend-users-list');

    if (modal && list) {
        // Clear previous content
        list.innerHTML = '<div class="loading">Loading...</div>';

        // Fetch trend users data
        fetch(`/api/trend_users/${trendType}/${encodeURIComponent(trendName)}`)
            .then(response => response.json())
            .then(data => {
                list.innerHTML = '';
                if (data.length === 0) {
                    list.innerHTML = '<p>No users found.</p>';
                } else {
                    data.forEach(user => {
                        const userItem = document.createElement('div');
                        userItem.className = 'user-list-item';
                        userItem.innerHTML = `
                            <img src="${user.profile_image_url}" alt="${user.username}" class="user-list-avatar">
                            <div class="user-list-info">
                                <h4><a href="/user/${user.id}" style="text-decoration: none; color: inherit;">${user.username}</a></h4>
                                <p>Click to view profile</p>
                            </div>
                        `;
                        list.appendChild(userItem);
                    });
                }
            })
            .catch(error => {
                console.error('Error loading trend users:', error);
                list.innerHTML = '<p>Error loading users.</p>';
            });

        modal.style.display = 'block';
    }
}

function closeTrendUsersModal() {
    const modal = document.getElementById('trend-users-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Trend Followers Modal Functions
function showTrendFollowersModal(trendType, trendName) {
    const modal = document.getElementById('trend-followers-modal');
    const list = document.getElementById('trend-followers-list');

    if (modal && list) {
        // Clear previous content
        list.innerHTML = '<div class="loading">Loading...</div>';

        // Fetch trend followers data
        fetch(`/api/trend_followers/${trendType}/${encodeURIComponent(trendName)}`)
            .then(response => response.json())
            .then(data => {
                list.innerHTML = '';
                if (data.length === 0) {
                    list.innerHTML = '<p>No followers found.</p>';
                } else {
                    data.forEach(user => {
                        const userItem = document.createElement('div');
                        userItem.className = 'user-list-item';
                        userItem.innerHTML = `
                            <img src="${user.profile_image_url}" alt="${user.username}" class="user-list-avatar">
                            <div class="user-list-info">
                                <h4><a href="/user/${user.id}" style="text-decoration: none; color: inherit;">${user.username}</a></h4>
                                <p>Click to view profile</p>
                            </div>
                        `;
                        list.appendChild(userItem);
                    });
                }
            })
            .catch(error => {
                console.error('Error loading trend followers:', error);
                list.innerHTML = '<p>Error loading followers.</p>';
            });

        modal.style.display = 'block';
    }
}

function closeTrendFollowersModal() {
    const modal = document.getElementById('trend-followers-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Logout confirmation functions
function confirmLogout(event) {
    event.preventDefault();
    const modal = document.getElementById('logout-modal');
    if (modal) {
        modal.style.display = 'block';
    }
}

function closeLogoutModal() {
    const modal = document.getElementById('logout-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function proceedLogout() {
    window.location.href = '/logout';
}

// Close modals when clicking outside
window.onclick = function(event) {
    const editModal = document.getElementById('edit-modal');
    const followersModal = document.getElementById('followers-modal');
    const followingModal = document.getElementById('following-modal');
    const trendUsersModal = document.getElementById('trend-users-modal');
    const trendFollowersModal = document.getElementById('trend-followers-modal');
    const logoutModal = document.getElementById('logout-modal');

    if (event.target === editModal) {
        editModal.style.display = 'none';
    }
    if (event.target === followersModal) {
        followersModal.style.display = 'none';
    }
    if (event.target === followingModal) {
        followingModal.style.display = 'none';
    }
    if (event.target === trendUsersModal) {
        trendUsersModal.style.display = 'none';
    }
    if (event.target === trendFollowersModal) {
        trendFollowersModal.style.display = 'none';
    }
    if (event.target === logoutModal) {
        logoutModal.style.display = 'none';
    }
}

// In app/static/js/main.js - Add this at the end of the file

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    const sortSelect = document.getElementById('sort-select');
    const mutualsContainer = document.getElementById('mutuals-container');
    
    if (!searchInput || !sortSelect || !mutualsContainer) return;

    // Store original cards for reset
    const originalCards = Array.from(mutualsContainer.children);
    let currentCards = [...originalCards];

    function filterAndSortUsers() {
        const searchTerm = searchInput.value.toLowerCase().trim();
        const sortBy = sortSelect.value;

        // Filter cards based on search term
        let filteredCards = originalCards.filter(card => {
            if (!searchTerm) return true;
            const username = card.querySelector('.user-link').textContent.toLowerCase();
            return username.includes(searchTerm);
        });

        // Sort cards
        filteredCards.sort((a, b) => {
            const aUsername = a.querySelector('.user-link').textContent.toLowerCase();
            const bUsername = b.querySelector('.user-link').textContent.toLowerCase();
            const aMatch = parseInt(a.querySelector('.match-score').textContent);
            const bMatch = parseInt(b.querySelector('.match-score').textContent);
            const aFollowers = parseInt(a.querySelector('.stat')?.textContent?.split(' ')[0]) || 0;
            const bFollowers = parseInt(b.querySelector('.stat')?.textContent?.split(' ')[0]) || 0;

            if (sortBy === 'alphabetical') return aUsername.localeCompare(bUsername);
            if (sortBy === 'followers') return bFollowers - aFollowers;
            return bMatch - aMatch; // Default: sort by match percentage
        });

        // Update display
        updateDisplay(filteredCards);
    }

    function updateDisplay(cards) {
        // Remove all current cards
        while (mutualsContainer.firstChild) {
            mutualsContainer.removeChild(mutualsContainer.firstChild);
        }

        // Add filtered and sorted cards
        const fragment = document.createDocumentFragment();
        cards.forEach(card => {
            fragment.appendChild(card.cloneNode(true));
        });

        mutualsContainer.appendChild(fragment);
        currentCards = [...cards];
    }

    // Event listeners
    searchInput.addEventListener('input', filterAndSortUsers);
    sortSelect.addEventListener('change', filterAndSortUsers);

    // Initialize
    filterAndSortUsers();
});