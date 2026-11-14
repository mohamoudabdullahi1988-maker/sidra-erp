<script setup>
import { computed, onBeforeUnmount, onMounted, ref, toRef, watch } from 'vue'
import { useRoute } from 'vue-router'

import { boot, navItems } from '../boot'
import { PRODUCT_NAME } from '../brand'
import { panel } from '../panel'

const ICONS = {
  dashboard: 'lucide-layout-dashboard',
  properties: 'lucide-building-2',
  customers: 'lucide-users',
  sales: 'lucide-handshake',
  contracts: 'lucide-file-text',
  collections: 'lucide-wallet',
  construction: 'lucide-hard-hat',
  setup: 'lucide-settings-2',
  finance: 'lucide-landmark',
}

const items = navItems()
const route = useRoute()
// The section of the page on screen; its list and record pages keep it highlighted.
const activeSection = computed(() => route.meta.section ?? route.name)

const navCollapsed = ref(false) // desktop: icon-only rail
const navDrawer = ref(false) // phone: slide-over
const panelOpen = toRef(panel, 'open') // desktop: column; phone: slide-over. Pages open it (panel.js).

function closeDrawers() {
  navDrawer.value = false
  if (window.matchMedia('(max-width: 1099px)').matches) panelOpen.value = false
}
function onKey(event) {
  if (event.key === 'Escape') closeDrawers()
}

watch(() => route.fullPath, () => (navDrawer.value = false))
onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onKey))
</script>

<template>
  <div class="shell" :class="{ 'shell--rail': navCollapsed, 'shell--panel': panelOpen }">
    <div v-if="navDrawer || panelOpen" class="scrim" @click="closeDrawers" />

    <aside class="nav" :class="{ 'nav--open': navDrawer }" aria-label="Main navigation">
      <div class="nav__brand">
        <span class="nav__mark" aria-hidden="true"><i /><i /><i /></span>
        <span class="nav__wordmark">{{ PRODUCT_NAME }}</span>
      </div>

      <nav class="nav__items">
        <RouterLink
          v-for="item in items"
          :key="item.key"
          :to="{ name: item.key }"
          class="nav__item"
          :class="{ 'nav__item--active': activeSection === item.key }"
          :aria-current="activeSection === item.key ? 'page' : undefined"
          :title="navCollapsed ? item.label : undefined"
        >
          <span class="nav__icon" :class="ICONS[item.key]" aria-hidden="true" />
          <span class="nav__label">{{ item.label }}</span>
        </RouterLink>
        <p v-if="!items.length" class="nav__none">No sections are available to your account.</p>
      </nav>

      <div class="nav__foot">
        <div class="nav__company" :title="boot.company || undefined">
          <span class="nav__icon lucide-building" aria-hidden="true" />
          <span class="nav__label">
            <small>Company</small>
            <strong>{{ boot.company || 'Not set' }}</strong>
          </span>
        </div>
        <button
          type="button"
          class="nav__collapse"
          :aria-label="navCollapsed ? 'Expand navigation' : 'Collapse navigation'"
          :aria-expanded="!navCollapsed"
          @click="navCollapsed = !navCollapsed"
        >
          <span class="nav__icon" :class="navCollapsed ? 'lucide-panel-left-open' : 'lucide-panel-left-close'" aria-hidden="true" />
          <span class="nav__label">Collapse</span>
        </button>
      </div>
    </aside>

    <div class="work">
      <header class="bar">
        <button type="button" class="bar__btn bar__btn--menu" aria-label="Open navigation" @click="navDrawer = true">
          <span class="lucide-menu" aria-hidden="true" />
        </button>
        <span class="bar__wordmark">{{ PRODUCT_NAME }}</span>
        <span class="bar__spacer" />
        <span class="bar__user" :title="boot.user.name">{{ boot.user.full_name }}</span>
        <button
          v-if="panel.inUse"
          type="button"
          class="bar__btn"
          :aria-label="panelOpen ? 'Close workflow' : 'Open workflow'"
          :aria-expanded="panelOpen"
          @click="panelOpen = !panelOpen"
        >
          <span class="workflow-label">Workflow</span>
          <span :class="panelOpen ? 'lucide-panel-right-close' : 'lucide-panel-right-open'" aria-hidden="true" />
        </button>
      </header>
      <main class="work__main">
        <slot />
      </main>
    </div>

    <aside class="panel" :class="{ 'panel--open': panelOpen }" aria-label="Side panel" :aria-hidden="!panelOpen">
      <div class="panel__head">
        <span class="bj-heading">Workflow</span>
        <button type="button" class="bar__btn" aria-label="Close side panel" @click="panelOpen = false">
          <span class="lucide-x" aria-hidden="true" />
        </button>
      </div>
      <!-- A page teleports its workflow panel here (ContractDetail.vue). -->
      <div id="berjaya-panel" class="panel__body" />
    </aside>
  </div>
</template>

<style scoped>
.shell {
  display: flex;
  height: 100%;
  min-height: 0;
}

/* ---- navigation ---- */
.nav {
  flex: none;
  width: var(--bj-nav-width);
  display: flex;
  flex-direction: column;
  background: var(--bj-charcoal);
  color: #fff;
  transition: width 0.16s ease;
  overflow: hidden;
}
.nav__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 56px;
  padding: 0 20px;
  flex: none;
}
.nav__mark {
  display: inline-flex;
  align-items: flex-end;
  gap: 3px;
  height: 18px;
  flex: none;
}
.nav__mark i {
  width: 5px;
  border-radius: 1px;
  background: var(--bj-terracotta-light);
}
.nav__mark i:nth-child(1) {
  height: 9px;
}
.nav__mark i:nth-child(2) {
  height: 18px;
  background: var(--bj-terracotta);
}
.nav__mark i:nth-child(3) {
  height: 13px;
}
.nav__wordmark,
.bar__wordmark {
  font-family: var(--bj-font-heading);
  font-size: 19px;
  font-weight: 600;
  letter-spacing: -0.01em;
}
.nav__items {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav__item,
.nav__collapse,
.nav__company {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 12px;
  border-radius: 8px;
  font-size: 14px;
  color: rgb(255 255 255 / 0.72);
  text-decoration: none;
  white-space: nowrap;
}
.nav__item:hover,
.nav__collapse:hover {
  background: rgb(255 255 255 / 0.07);
  color: #fff;
}
.nav__item--active,
.nav__item--active:hover {
  background: var(--bj-terracotta);
  color: #fff;
  font-weight: 500;
}
.nav__icon {
  width: 18px;
  height: 18px;
  flex: none;
}
.nav__none {
  margin: 8px 12px;
  font-size: 13px;
  line-height: 1.5;
  color: rgb(255 255 255 / 0.6);
  white-space: normal;
}
.nav__foot {
  flex: none;
  padding: 10px;
  border-top: 1px solid rgb(255 255 255 / 0.1);
}
.nav__company .nav__label {
  display: flex;
  flex-direction: column;
  min-width: 0;
  line-height: 1.25;
}
.nav__company small {
  font-size: 11px;
  color: rgb(255 255 255 / 0.5);
}
.nav__company strong {
  font-weight: 500;
  color: #fff;
  overflow: hidden;
  text-overflow: ellipsis;
}
.nav__collapse {
  width: 100%;
  border: 0;
  background: none;
  cursor: pointer;
  text-align: left;
}

.shell--rail .nav {
  width: var(--bj-nav-width-collapsed);
}
.shell--rail .nav__label,
.shell--rail .nav__wordmark,
.shell--rail .nav__none {
  display: none;
}
.shell--rail .nav__brand {
  padding: 0;
  justify-content: center;
}
.shell--rail .nav__item,
.shell--rail .nav__collapse,
.shell--rail .nav__company {
  justify-content: center;
  padding: 9px 0;
}

/* ---- workspace ---- */
.work {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}
.bar {
  flex: none;
  height: 56px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 16px;
  background: var(--bj-card);
  border-bottom: 1px solid var(--bj-line);
}
.bar__spacer {
  flex: 1;
}
.bar__wordmark {
  display: none;
  color: var(--bj-ink);
}
.bar__user {
  font-size: 13px;
  color: var(--bj-muted);
  max-width: 40vw;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bar__btn {
  display: inline-grid;
  place-items: center;
  min-width: 44px;
  min-height: 44px;
  border: 0;
  border-radius: 8px;
  background: none;
  color: var(--bj-muted);
  cursor: pointer;
}
.bar__btn:hover {
  background: var(--bj-ground);
  color: var(--bj-ink);
}
.bar__btn > span {
  width: 18px;
  height: 18px;
}
.bar__btn--menu {
  display: none;
}
.work__main {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

/* ---- right panel ---- */
.panel {
  flex: none;
  width: 0;
  overflow: hidden;
  background: var(--bj-card);
  border-left: 0 solid var(--bj-line);
  display: flex;
  flex-direction: column;
  transition: width 0.16s ease;
  visibility: hidden;
}
.panel--open {
  width: var(--bj-panel-width);
  border-left-width: 1px;
  visibility: visible;
}
.panel__head {
  flex: none;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 8px 0 16px;
  border-bottom: 1px solid var(--bj-line);
  font-size: 15px;
  font-weight: 600;
  min-width: var(--bj-panel-width);
}
.panel__body {
  flex: 1;
  min-height: 0;
  overflow: auto;
  min-width: var(--bj-panel-width);
}

.panel__body:empty::before {
  content: 'Nothing to show for this page yet.';
  display: block;
  padding: 16px;
  font-size: 13px;
  color: var(--bj-muted);
}

.scrim {
  display: none;
}

/* ---- below 1100px the right panel is a drawer ---- */
@media (max-width: 1099px) {
  .panel {
    position: fixed;
    inset: 0 0 0 auto;
    z-index: 40;
    width: min(var(--bj-panel-width), 88vw);
    border-left-width: 1px;
    transform: translateX(100%);
    transition: transform 0.18s ease, visibility 0.18s;
  }
  .panel--open {
    transform: none;
  }
  .panel__head,
  .panel__body {
    min-width: 0;
  }
  .scrim {
    display: block;
    position: fixed;
    inset: 0;
    z-index: 30;
    background: rgb(31 35 38 / 0.45);
  }
}

/* ---- phone: navigation is a drawer too ---- */
@media (max-width: 799px) {
  .nav,
  .shell--rail .nav {
    position: fixed;
    inset: 0 auto 0 0;
    z-index: 40;
    width: min(var(--bj-nav-width), 82vw);
    transform: translateX(-100%);
    transition: transform 0.18s ease;
  }
  .nav--open {
    transform: none;
  }
  /* The rail has no meaning in a drawer: always show labels. */
  .shell--rail .nav__label,
  .shell--rail .nav__wordmark {
    display: revert;
  }
  .shell--rail .nav__company .nav__label {
    display: flex;
  }
  .shell--rail .nav__brand {
    padding: 0 20px;
    justify-content: flex-start;
  }
  .shell--rail .nav__item,
  .shell--rail .nav__company {
    justify-content: flex-start;
    padding: 9px 12px;
  }
  .nav__collapse {
    display: none;
  }
  .bar__btn--menu {
    display: inline-grid;
  }
  .bar__wordmark {
    display: inline;
  }
}
@media (min-width: 1100px) {
  .scrim {
    display: none;
  }
}
</style>

<style scoped>
.bar__btn:has(.workflow-label) { display: flex; gap: 8px; padding: 8px; }
.bar__btn > .workflow-label { width: auto; height: auto; }
</style>
