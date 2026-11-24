const form = document.querySelector('#task-form');
const tasks = document.querySelector('#tasks');
const message = document.querySelector('#message');
const cancel = document.querySelector('#cancel');
const labels = {pending: 'Belum dikerjakan', in_progress: 'Dikerjakan', completed: 'Selesai'};
let editing = null;

function resetForm() {
  editing = null;
  form.reset();
  document.querySelector('#form-title').textContent = 'Tambah tugas';
  cancel.hidden = true;
}

async function request(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) throw new Error(response.status === 404 ? 'Tugas tidak ditemukan.' : 'Gagal memproses permintaan. Periksa koneksi dan coba lagi.');
  return response.status === 204 ? null : response.json();
}

async function loadTasks() {
  tasks.textContent = 'Memuat tugas...';
  try {
    const data = await request('/tasks');
    tasks.replaceChildren();
    document.querySelector('#count').textContent = `${data.length} tugas`;
    if (!data.length) tasks.textContent = 'Anda belum memiliki tugas. Tambahkan tugas pertama anda.';
    for (const task of data) {
      const item = document.createElement('article');
      item.className = 'task';
      const info = document.createElement('div');
      const heading = document.createElement('h3');
      heading.textContent = task.title;
      const course = document.createElement('p');
      course.textContent = task.course;
      const details = document.createElement('p');
      details.className = 'details';
      details.textContent = `Deadline ${task.due_date} | ${labels[task.status]}`;
      info.append(heading, course, details);
      const actions = document.createElement('div');
      actions.className = 'task-actions';
      const edit = document.createElement('button');
      edit.className = 'secondary';
      edit.textContent = 'Edit';
      edit.setAttribute('aria-label', `Edit ${task.title}`);
      edit.onclick = () => {
        editing = task.id;
        for (const key of ['title', 'course', 'due_date', 'status']) form.elements[key].value = task[key];
        document.querySelector('#form-title').textContent = 'Edit tugas';
        cancel.hidden = false;
        form.elements.title.focus();
      };
      const remove = document.createElement('button');
      remove.className = 'secondary';
      remove.textContent = 'Hapus';
      remove.setAttribute('aria-label', `Hapus ${task.title}`);
      remove.onclick = async () => {
        if (!confirm(`Hapus tugas "${task.title}"?`)) return;
        try {
          await request(`/tasks/${task.id}`, {method: 'DELETE'});
          if (editing === task.id) resetForm();
          message.textContent = 'Tugas dihapus.';
          await loadTasks();
        } catch (error) { message.textContent = error.message; }
      };
      actions.append(edit, remove);
      item.append(info, actions);
      tasks.append(item);
    }
  } catch (error) {
    tasks.textContent = '';
    document.querySelector('#count').textContent = '';
    message.textContent = error.message;
  }
}

cancel.onclick = resetForm;
form.onsubmit = async event => {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(form));
  data.title = data.title.trim();
  data.course = data.course.trim();
  if (!data.title || !data.course) { message.textContent = 'Nama tugas dan mata kuliah wajib diisi.'; return; }
  const submit = form.querySelector('[type=submit]');
  submit.disabled = true;
  try {
    await request(editing === null ? '/tasks' : `/tasks/${editing}`, {
      method: editing === null ? 'POST' : 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)
    });
    message.textContent = editing === null ? 'Tugas ditambahkan.' : 'Tugas diperbarui.';
    resetForm();
    await loadTasks();
  } catch (error) { message.textContent = error.message; }
  finally { submit.disabled = false; }
};
loadTasks();
