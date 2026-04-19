let complaints = []
let currentUser = null

// Check if user is logged in
async function checkAuth() {
    const token = localStorage.getItem('token')
    if (token) {
        // In a real app, you'd validate the token
        currentUser = JSON.parse(localStorage.getItem('user'))
    }
    updateAdminLink()
}

function updateAdminLink() {
    const adminLink = document.querySelector('.admin-link')
    if (adminLink) {
        adminLink.style.display = 'inline'  // Always show admin panel link to allow access
    }
}

async function login() {
    // try using login page fields if available
    let idElement = document.getElementById('studentId')
    let pwElement = document.getElementById('password')
    let username = idElement ? idElement.value.trim() : ''
    let password = pwElement ? pwElement.value : ''

    if (!username || !password) {
        // fallback for index prompt flow
        username = prompt("Enter username")
        if (!username) return
        password = prompt("Enter password") || ''
    }

    try {
        const response = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ student_id: username, password: password })
        })
        const result = await response.json()
        if (result.success) {
            currentUser = result.user
            localStorage.setItem("user", JSON.stringify(currentUser))
            localStorage.setItem("token", "dummy-token")
            alert("Logged in as " + username)
            updateAdminLink()
            loadComplaints()
            if (location.pathname.endsWith('login.html')) {
                window.location.href = 'index.html'
            }
        } else {
            alert("Login failed: invalid credentials")
            let error = document.getElementById('errorMsg')
            if (error) error.style.display = 'block'
        }
    } catch (error) {
        console.error('Login error:', error)
        alert('Login error, please try again')
    }
}

function showSkeleton() {
    const container = document.getElementById("posts")
    container.innerHTML = ""
    for (let i = 0; i < 5; i++)
        container.innerHTML += `<div class="skeleton"></div>`
}

async function loadComplaints(category = 'All', sort = 'new') {
    showSkeleton()
    try {
        const response = await fetch(`/api/complaints?category=${category}&sort=${sort}`)
        complaints = await response.json()
        renderPosts()
    } catch (error) {
        console.error('Error loading complaints:', error)
        renderPosts()  // Render with empty or cached data
    }
}

function renderPosts() {
    const container = document.getElementById("posts")
    container.innerHTML = ""

    complaints.forEach(c => {
        const karma = c.votes > 10 ? "hot" : ""
        let mediaHTML = ""
        if (c.media && c.media.length > 0) {
            mediaHTML = `<div class="gallery">`
            c.media.forEach(m => {
                const mimeType = m.type === "image" ? "image" : "video"
                const extension = m.filename.split('.').pop()
                if (m.type === "image") {
                    mediaHTML += `<img src="data:${mimeType}/${extension};base64,${m.data}" onclick="openViewer('data:${mimeType}/${extension};base64,${m.data}')">`
                } else if (m.type === "video") {
                    mediaHTML += `<video controls src="data:${mimeType}/${extension};base64,${m.data}"></video>`
                }
            })
            mediaHTML += `</div>`
        }

        container.innerHTML += `
        <div class="post">
            <div class="vote">
                <button class="up" onclick="vote(${c.id}, 1)">⬆</button>
                <span class="${karma}">${c.votes}</span>
                <button class="down" onclick="vote(${c.id}, -1)">⬇</button>
            </div>
            <div class="content">
                <span class="tag">${c.category}</span>
                <span class="status status-${c.status ? c.status.toLowerCase() : 'pending'}">${c.status || 'Pending'}</span>
                <h3>${c.title}</h3>
                <div class="author">Posted by ${c.author}</div>
                ${c.status === 'Rejected' && c.rejection_reason ? `<div class="rejection-reason-display"><strong>Rejection Reason:</strong> ${c.rejection_reason}</div>` : ''}
                ${mediaHTML}
                <input placeholder="comment..." onkeypress="addComment(event, ${c.id})">
                <div>
                    ${c.comments ? c.comments.map(cm => `<div class="comment">${cm.text} - ${cm.author}</div>`).join("") : ""}
                </div>
                ${currentUser && (c.author === currentUser.student_id || currentUser.is_admin) ? `<button class="delete-btn" onclick="deletePost(${c.id})">Delete</button>` : ""}
            </div>
        </div>`
    })

    renderTrending()
}

async function vote(id, v) {
    if (!currentUser) {
        alert("Login required to vote")
        return
    }

    try {
        const response = await fetch(`/api/complaints/${id}/vote`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: currentUser.id, vote_type: v })
        })
        const result = await response.json()
        if (result.success) {
            // Update local data
            const complaint = complaints.find(c => c.id === id)
            if (complaint) complaint.votes = result.votes
            renderPosts()
        }
    } catch (error) {
        console.error('Error voting:', error)
    }
}

async function deletePost(id) {
    if (!confirm("Delete this complaint?")) return

    try {
        const response = await fetch(`/api/complaints/${id}`, { method: 'DELETE' })
        if (response.ok) {
            const result = await response.json()
            if (result.success) {
                alert('Complaint deleted successfully')
                loadComplaints()  // Reload all complaints
            } else {
                alert('Failed to delete complaint')
            }
        } else {
            alert('Error: ' + response.status)
        }
    } catch (error) {
        console.error('Error deleting post:', error)
        alert('Error deleting complaint: ' + error.message)
    }
}

async function addComment(e, id) {
    if (e.key === "Enter" && e.target.value.trim()) {
        try {
            const response = await fetch(`/api/complaints/${id}/comment`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: e.target.value, author: currentUser ? currentUser.student_id : 'Anonymous' })
            })
            if (response.ok) {
                e.target.value = ""
                loadComplaints()  // Reload to get updated comments
            }
        } catch (error) {
            console.error('Error adding comment:', error)
        }
    }
}

function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result)
        reader.onerror = reject
        reader.readAsDataURL(blob)
    })
}

function toggleMode() {
    document.body.classList.toggle("light")
}

function calculateTrending() {
    return complaints.map(c => {
        const hours = (Date.now() - new Date(c.created_at).getTime()) / 3600000
        const score = c.votes / (hours + 2)
        return { ...c, score }
    }).sort((a, b) => b.score - a.score).slice(0, 5)
}

function renderTrending() {
    const list = document.getElementById("trending")
    const t = calculateTrending()
    list.innerHTML = ""
    t.forEach(p => {
        list.innerHTML += `<div>${p.title}</div>`
    })
}

function openViewer(src) {
    const viewer = document.getElementById("imageViewer")
    const img = document.getElementById("viewerImage")
    img.src = src
    viewer.style.display = "flex"
    viewer.onclick = () => viewer.style.display = "none"
}

function filterCategory(category) {
    loadComplaints(category)
}

function sortPosts(sort) {
    loadComplaints('All', sort)
}

// Initialize
checkAuth()
loadComplaints()

// Theme toggle
const themeToggle = document.getElementById('theme-toggle')
if (themeToggle) {
    themeToggle.addEventListener('change', () => {
        document.body.classList.toggle('light')
        document.body.classList.toggle('dark')
        const slider = document.querySelector('.slider')
        if (document.body.classList.contains('dark')) {
            slider.classList.add('dark')
        } else {
            slider.classList.remove('dark')
        }
    })
    // Set initial state
    if (document.body.classList.contains('dark')) {
        themeToggle.checked = false
        document.querySelector('.slider').classList.add('dark')
    } else {
        themeToggle.checked = true
        document.querySelector('.slider').classList.remove('dark')
    }
}
