<script setup>
import { ref, watch } from 'vue'

import { apiGet, apiPost } from '../api'

// A unit's or job's map point (api/locations.py): shown, opened in Google Maps or Earth, exported as
// KML, and set by coordinates or from this device's current position. The server checks the
// values, the user's write permission and the record's version.
const props = defineProps({
  doctype: { type: String, required: true },
  name: { type: String, required: true },
})

const API = 'sidra_realestate.api.locations.'
const location = ref(null)
const error = ref('')
const editing = ref(false)
const lat = ref('')
const lng = ref('')
const busy = ref(false)
const actionError = ref('')
const saved = ref(false)

async function load() {
  error.value = ''
  try {
    const response = await apiGet('/api/method/' + API + 'get_location', { doctype: props.doctype, name: props.name })
    location.value = response.message
  } catch (err) {
    location.value = null
    error.value = err.message || 'The location could not be loaded.'
  }
}

function edit() {
  lat.value = location.value?.latitude ?? ''
  lng.value = location.value?.longitude ?? ''
  actionError.value = ''
  saved.value = false
  editing.value = true
}

function here() {
  actionError.value = ''
  if (!navigator.geolocation) {
    actionError.value = 'This device cannot report its position.'
    return
  }
  busy.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      lat.value = position.coords.latitude.toFixed(6)
      lng.value = position.coords.longitude.toFixed(6)
      busy.value = false
    },
    () => {
      actionError.value = 'Your position could not be read. Allow location access, or type the coordinates.'
      busy.value = false
    },
    { enableHighAccuracy: true, timeout: 15000 },
  )
}

async function save() {
  busy.value = true
  actionError.value = ''
  try {
    const response = await apiPost(API + 'set_location', {
      doctype: props.doctype,
      name: props.name,
      latitude: lat.value,
      longitude: lng.value,
      expected_modified: location.value.modified,
    })
    location.value = response
    editing.value = false
    saved.value = true
  } catch (err) {
    actionError.value = err.message || 'The location was not saved.'
  } finally {
    busy.value = false
  }
}

const kml = () =>
  `/api/method/${API}export_kml?doctype=${encodeURIComponent(props.doctype)}&name=${encodeURIComponent(props.name)}`

watch(() => [props.doctype, props.name], load, { immediate: true })
</script>

<template>
  <section class="bj-section" aria-label="Location">
    <h2>Location</h2>
    <div class="page__card bj-card lp">
      <p v-if="error" class="bj-muted" role="status">{{ error }}</p>
      <template v-else-if="location">
        <p v-if="!location.configured" class="bj-muted">The location field is not installed on this site.</p>
        <template v-else>
          <p v-if="location.latitude !== null" class="lp__point">
            <span class="lucide-map-pin" aria-hidden="true" />
            <strong>{{ location.latitude }}, {{ location.longitude }}</strong>
            <span v-if="location.source === 'legacy_gps'" class="bj-muted">(from the older GPS text)</span>
          </p>
          <p v-else-if="location.unsupported_geometry" class="bj-muted">A shape other than a single point is recorded; it is kept as it is.</p>
          <p v-else class="bj-muted">No location recorded.</p>
          <p v-if="saved" class="bj-note lp__ok" role="status"><span class="lucide-circle-check-big" aria-hidden="true" />Location saved.</p>
          <div class="bj-toolbar">
            <a v-if="location.links" class="bj-btn" :href="location.links.maps" target="_blank" rel="noopener"><span class="lucide-map" aria-hidden="true" />Google Maps</a>
            <a v-if="location.links" class="bj-btn" :href="location.links.earth" target="_blank" rel="noopener"><span class="lucide-globe" aria-hidden="true" />Google Earth</a>
            <a v-if="location.latitude !== null" class="bj-btn" :href="kml()"><span class="lucide-download" aria-hidden="true" />KML</a>
            <button v-if="location.can_write && !editing" type="button" class="bj-btn" @click="edit"><span class="lucide-pencil" aria-hidden="true" />Set location</button>
          </div>
          <form v-if="editing" class="lp__form" @submit.prevent="save">
            <label class="lp__field"><span>Latitude</span><input v-model="lat" class="bj-input" inputmode="decimal" aria-label="Latitude" /></label>
            <label class="lp__field"><span>Longitude</span><input v-model="lng" class="bj-input" inputmode="decimal" aria-label="Longitude" /></label>
            <div class="bj-toolbar lp__actions">
              <button type="button" class="bj-btn" :disabled="busy" @click="here"><span class="lucide-locate-fixed" aria-hidden="true" />Use my current position</button>
              <button type="submit" class="bj-btn bj-btn--primary" :disabled="busy">Save location</button>
              <button type="button" class="bj-btn" :disabled="busy" @click="editing = false">Cancel</button>
            </div>
          </form>
          <p v-if="actionError" class="lp__error" role="alert"><span class="lucide-triangle-alert" aria-hidden="true" />{{ actionError }}</p>
          <p class="bj-foot">A recorded point, not surveyed parcel boundaries.</p>
        </template>
      </template>
      <p v-else class="bj-muted" role="status">Loading…</p>
    </div>
  </section>
</template>

<style scoped>
.lp__point {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 12px;
}
.lp__form {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px 16px;
  margin-top: 16px;
}
.lp__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--bj-muted);
}
.lp__field .bj-input {
  width: 100%;
}
.lp__actions {
  grid-column: 1 / -1;
}
.lp__error {
  margin: 8px 0 0;
  color: var(--bj-state-blocked);
}
.lp__ok {
  margin: 0 0 12px;
}
.lp__ok > span {
  color: var(--bj-state-completed);
}
</style>
