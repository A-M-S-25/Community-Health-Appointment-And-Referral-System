const baseHeaders = () => ({'Content-Type': 'application/json'});

function setAlert(elementId, message, isSuccess = true) {
  const el = document.getElementById(elementId);
  if (!el) return;
  el.classList.remove('d-none', 'alert-danger', 'alert-success');
  el.classList.add(isSuccess ? 'alert-success' : 'alert-danger');
  el.textContent = message;
}

function handleError(elementId, error) {
  setAlert(elementId, error || 'Something went wrong.', false);
}

document.addEventListener('DOMContentLoaded', () => {
  const registrationForm = document.getElementById('registration-form');
  const bookingForm = document.getElementById('booking-form');
  const availabilityButton = document.getElementById('check-availability');
  const queue = document.getElementById('referral-queue');
  const queueStatus = document.getElementById('queue-status');

  async function loadReferralQueue() {
    if (!queue) return;
    const query = queueStatus.value ? `?status=${encodeURIComponent(queueStatus.value)}` : '';
    const response = await fetch(`/api/v1/referrals${query}`, {credentials: 'same-origin'});
    const result = await response.json();
    if (!response.ok) {
      queue.innerHTML = `<tr><td colspan="5" class="text-danger">${result.error || 'Unable to load queue.'}</td></tr>`;
      return;
    }
    queue.innerHTML = result.map(item => `
      <tr>
        <td>#${item.referral_id}</td>
        <td><a href="/patients/${item.patient_id}">${item.patient_name}</a></td>
        <td><span class="badge bg-primary">${item.status}</span></td>
        <td>${item.destination_facility}</td>
        <td><a href="/referrals/${item.referral_id}">View</a></td>
      </tr>
    `).join('') || '<tr><td colspan="5" class="text-muted text-center">No referrals found.</td></tr>';
  }

  if (queueStatus) {
    queueStatus.addEventListener('change', loadReferralQueue);
    loadReferralQueue();
  }

  if (registrationForm) {
    registrationForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(registrationForm);
      const payload = {
        phone_number: formData.get('phone_number'),
        demographics: {
          name: formData.get('patient_name'),
          age: formData.get('age')
        },
      };

      const response = await fetch('/api/v1/patients/onboard', {
        method: 'POST',
        headers: {...baseHeaders(), 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''},
        credentials: 'same-origin',
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      if (!response.ok) {
        handleError('response', result.error || 'Unable to onboard patient.');
        return;
      }

      setAlert('response', `Patient onboarded: ${result.message}`);
    });
  }

  if (bookingForm) {
    bookingForm.addEventListener('submit', async (event) => {
      event.preventDefault();
      const formData = new FormData(bookingForm);
      const payload = {
        referral_id: Number(formData.get('referral_id')),
        appointment_id: Number(formData.get('appointment_id'))
      };

      const response = await fetch('/api/v1/appointments/confirm', {
        method: 'POST',
        headers: {...baseHeaders(), 'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''},
        credentials: 'same-origin',
        body: JSON.stringify(payload)
      });

      const result = await response.json();
      if (!response.ok) {
        handleError('booking-response', result.error || 'Unable to confirm booking.');
        return;
      }

      setAlert('booking-response', `Booking confirmed: ${result.status}`);
    });
  }

  if (availabilityButton) {
    availabilityButton.addEventListener('click', async () => {
      const tierLevel = document.getElementById('tier-level').value;
      const location = document.getElementById('location').value;
      const query = new URLSearchParams();
      if (tierLevel) query.set('tier_level', tierLevel);
      if (location) query.set('location', location);

      const response = await fetch(`/api/v1/facilities/availability?${query.toString()}`);
      const result = await response.json();
      const container = document.getElementById('availability-result');
      if (!Array.isArray(result)) {
        container.innerHTML = '<div class="alert alert-danger">Unable to fetch availability.</div>';
        return;
      }

      container.innerHTML = result.map(f => `
        <div class="border rounded p-2 mb-2">
          <strong>${f.name}</strong><br>
          Tier ${f.tier_level} • ${f.available_capacity} of ${f.capacity} beds available • ${f.available_slots} appointment slots
        </div>
      `).join('') || '<div class="alert alert-warning">No matching facilities found.</div>';
    });
  }
});
