// KMD Dashboard JavaScript

const API_BASE = '/api';

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
  loadMetrics();
  loadLeads();
  loadPosts();
  loadWhatsAppStats();
  loadSchedulerStats();

  // Refresh metrics every 30 seconds
  setInterval(loadMetrics, 30000);
  setInterval(loadLeads, 60000);
  setInterval(loadPosts, 60000);
});

// Tab switching
function switchTab(tabName) {
  // Hide all tab contents
  document.querySelectorAll('.tab-content').forEach(tab => {
    tab.classList.remove('active');
  });
  // Remove active class from all buttons
  document.querySelectorAll('.tab-button').forEach(btn => {
    btn.classList.remove('active');
  });
  // Show selected tab
  const tabElement = document.getElementById(tabName);
  if (tabElement) {
    tabElement.classList.add('active');
  }
  // Mark button as active
  event.target.classList.add('active');
}

// Load and display metrics
async function loadMetrics() {
  try {
    const response = await fetch(`${API_BASE}/analytics/summary`);
    const data = await response.json();
    
    document.getElementById('totalLeads').textContent = data.total_leads || 0;
    document.getElementById('newLeads').textContent = data.new_leads || 0;
    document.getElementById('publishedPosts').textContent = data.published_posts || 0;
    document.getElementById('scheduledPosts').textContent = data.scheduled_posts || 0;
  } catch (error) {
    console.error('Error loading metrics:', error);
  }
}

// Load and display leads
async function loadLeads() {
  try {
    const response = await fetch(`${API_BASE}/leads`);
    const leads = await response.json();
    
    const container = document.getElementById('leadsContainer');
    if (!leads || leads.length === 0) {
      container.innerHTML = '<p style="text-align: center; color: #94a3b8; padding: 20px;">No leads yet</p>';
      return;
    }

    container.innerHTML = leads.map(lead => `
      <div class="list-item">
        <div class="item-content">
          <div class="item-label">Name</div>
          <div class="item-value">${lead.name}</div>
          <div class="item-label" style="margin-top: 8px;">Phone</div>
          <div class="item-value">${lead.phone}</div>
        </div>
        <div>
          <span class="badge badge-${lead.status}">${lead.status}</span>
          <div class="action-buttons" style="margin-top: 8px;">
            <button class="btn-small" onclick="sendWelcome(${lead.id}, '${lead.name}')">Welcome</button>
            <button class="btn-small" onclick="viewLead(${lead.id})">Details</button>
          </div>
        </div>
      </div>
    `).join('');
  } catch (error) {
    console.error('Error loading leads:', error);
  }
}

// Load and display posts
async function loadPosts() {
  try {
    const response = await fetch(`${API_BASE}/scheduler/posts`);
    const posts = await response.json();
    
    const container = document.getElementById('postsContainer');
    if (!posts || posts.length === 0) {
      container.innerHTML = '<p style="text-align: center; color: #94a3b8; padding: 20px;">No posts scheduled</p>';
      return;
    }

    container.innerHTML = posts.slice(0, 10).map(post => `
      <div class="list-item">
        <div class="item-content">
          <div class="item-label">Platform</div>
          <div class="item-value">${post.platform.toUpperCase()}</div>
          <div class="item-label" style="margin-top: 8px;">Caption</div>
          <div class="item-value" style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${post.caption}</div>
          <div class="item-label" style="margin-top: 8px;">Scheduled</div>
          <div class="item-value">${post.scheduled_for ? new Date(post.scheduled_for).toLocaleString() : 'Not set'}</div>
        </div>
        <div>
          <span class="badge badge-${post.status}">${post.status}</span>
          <div class="action-buttons" style="margin-top: 8px;">
            <button class="btn-small" onclick="publishPost(${post.id})">Publish</button>
            <button class="btn-small" onclick="editPost(${post.id})">Edit</button>
          </div>
        </div>
      </div>
    `).join('');
  } catch (error) {
    console.error('Error loading posts:', error);
  }
}

// Load WhatsApp statistics
async function loadWhatsAppStats() {
  try {
    const response = await fetch(`${API_BASE}/whatsapp/stats`);
    const stats = await response.json();
    
    document.getElementById('whatsappStats').innerHTML = `
      <div class="stats-display">
        <div class="stat-item">
          <div class="stat-number">${stats.total_leads || 0}</div>
          <div class="stat-label">Total Leads</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">${stats.new_leads || 0}</div>
          <div class="stat-label">New Leads</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">${stats.total_messages || 0}</div>
          <div class="stat-label">Messages</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">${stats.engagement_rate || '0%'}</div>
          <div class="stat-label">Engagement</div>
        </div>
      </div>
    `;
  } catch (error) {
    console.error('Error loading WhatsApp stats:', error);
  }
}

// Load scheduler statistics
async function loadSchedulerStats() {
  try {
    const response = await fetch(`${API_BASE}/scheduler/stats`);
    const stats = await response.json();
    
    document.getElementById('schedulerStats').innerHTML = `
      <div class="stats-display">
        <div class="stat-item">
          <div class="stat-number">${stats.total_posts || 0}</div>
          <div class="stat-label">Total Posts</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">${stats.published || 0}</div>
          <div class="stat-label">Published</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">${stats.scheduled || 0}</div>
          <div class="stat-label">Scheduled</div>
        </div>
        <div class="stat-item">
          <div class="stat-number">${stats.draft || 0}</div>
          <div class="stat-label">Draft</div>
        </div>
      </div>
    `;
  } catch (error) {
    console.error('Error loading scheduler stats:', error);
  }
}

// Create a new lead
async function createLead() {
  const payload = {
    name: document.getElementById('leadName').value,
    phone: document.getElementById('leadPhone').value,
    email: document.getElementById('leadEmail').value,
    source: document.getElementById('leadSource').value || 'website',
    interest: document.getElementById('leadInterest').value,
    notes: document.getElementById('leadNotes').value,
  };

  if (!payload.name || !payload.phone) {
    showAlert('Please fill in name and phone', 'error');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/leads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      showAlert('Lead created successfully!', 'success');
      document.getElementById('leadForm').reset();
      loadLeads();
      loadMetrics();
    } else {
      const error = await response.json();
      showAlert(error.detail || 'Error creating lead', 'error');
    }
  } catch (error) {
    showAlert('Error creating lead: ' + error.message, 'error');
  }
}

// Schedule a new post
async function schedulePost() {
  const payload = {
    platform: document.getElementById('postPlatform').value,
    caption: document.getElementById('postCaption').value,
    media_url: document.getElementById('postMediaUrl').value,
    scheduled_for: document.getElementById('postScheduledFor').value ? new Date(document.getElementById('postScheduledFor').value).toISOString() : null,
    status: 'scheduled',
  };

  if (!payload.platform || !payload.caption) {
    showAlert('Please fill in platform and caption', 'error');
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/scheduler/posts`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (response.ok) {
      showAlert('Post scheduled successfully!', 'success');
      document.getElementById('postForm').reset();
      loadPosts();
      loadMetrics();
    } else {
      const error = await response.json();
      showAlert(error.detail || 'Error scheduling post', 'error');
    }
  } catch (error) {
    showAlert('Error scheduling post: ' + error.message, 'error');
  }
}

// Send welcome message to lead
async function sendWelcome(leadId, leadName) {
  try {
    const response = await fetch(`${API_BASE}/whatsapp/welcome/${leadId}`, {
      method: 'POST',
    });

    if (response.ok) {
      showAlert(`Welcome message sent to ${leadName}!`, 'success');
    } else {
      showAlert('Error sending welcome message', 'error');
    }
  } catch (error) {
    showAlert('Error: ' + error.message, 'error');
  }
}

// Publish a post immediately
async function publishPost(postId) {
  if (!confirm('Publish this post now?')) return;

  try {
    const response = await fetch(`${API_BASE}/scheduler/posts/${postId}/publish`, {
      method: 'POST',
    });

    if (response.ok) {
      showAlert('Post published!', 'success');
      loadPosts();
      loadMetrics();
    } else {
      showAlert('Error publishing post', 'error');
    }
  } catch (error) {
    showAlert('Error: ' + error.message, 'error');
  }
}

// View lead details
async function viewLead(leadId) {
  try {
    const response = await fetch(`${API_BASE}/leads`);
    const leads = await response.json();
    const lead = leads.find(l => l.id === leadId);
    
    if (lead) {
      alert(`Lead: ${lead.name}\nPhone: ${lead.phone}\nEmail: ${lead.email || 'N/A'}\nStatus: ${lead.status}\nSource: ${lead.source}`);
    }
  } catch (error) {
    showAlert('Error loading lead details', 'error');
  }
}

// Edit post (placeholder)
async function editPost(postId) {
  alert('Edit functionality coming soon!');
}

// Show alert message
function showAlert(message, type = 'success') {
  const alertDiv = document.createElement('div');
  alertDiv.className = `alert alert-${type}`;
  alertDiv.textContent = message;
  alertDiv.style.position = 'fixed';
  alertDiv.style.top = '20px';
  alertDiv.style.right = '20px';
  alertDiv.style.zIndex = '2000';
  alertDiv.style.maxWidth = '400px';
  document.body.appendChild(alertDiv);

  setTimeout(() => {
    alertDiv.remove();
  }, 5000);
}
