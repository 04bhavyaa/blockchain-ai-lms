// Courses Logic

async function loadCourses() {
  try {
    checkAuth();
    showLoading(true);

    const courses = await api.getCourses();
    displayCourses(courses);

  } catch (error) {
    showNotification('Failed to load courses: ' + error.message, 'error');
  } finally {
    showLoading(false);
  }
}

function displayCourses(courses) {
  const container = document.getElementById('courses-container');
  container.innerHTML = courses.map(course => `
    <div class="course-card">
      <img src="${course.thumbnail_url || 'https://via.placeholder.com/300x200'}" alt="${course.title}">
      <div class="course-info">
        <h3>${course.title}</h3>
        <p class="instructor">👨‍🏫 ${course.instructor_name}</p>
        <p class="description">${course.description?.substring(0, 100)}...</p>
        
        <div class="course-meta">
          <span>⭐ ${course.average_rating || 'N/A'}/5</span>
          <span>👥 ${course.total_enrollments}</span>
          <span>⏱️ ${course.duration_hours}h</span>
        </div>

        <div class="course-footer">
          ${course.access_type === 'free' ? 
            '<span class="tag-free">FREE</span>' : 
            '<span class="tag-paid">💰 ' + (course.token_cost || course.price_usd) + '</span>'
          }
          <button onclick="enrollCourse(${course.id})">Enroll</button>
        </div>
      </div>
    </div>
  `).join('');
}

async function enrollCourse(courseId) {
  try {
    showLoading(true);
    await api.enrollCourse(courseId);
    showNotification('Successfully enrolled!', 'success');
    setTimeout(() => loadCourses(), 1000);
  } catch (error) {
    showNotification('Enrollment failed: ' + error.message, 'error');
  } finally {
    showLoading(false);
  }
}

window.addEventListener('load', loadCourses);
console.log('✅ Courses loaded');