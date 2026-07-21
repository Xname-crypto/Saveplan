<script setup lang="ts">
import { ArrowLeft, X } from 'lucide-vue-next';
import { computed, nextTick, ref, watch } from 'vue';
import { useRouter } from '@/router';

const router = useRouter();
const videoReady = ref(false);
const videoErrored = ref(false);
const videoRef = ref<HTMLVideoElement | null>(null);

const props = defineProps<{
  videoSrc?: string;
  posterSrc?: string;
  showBack?: boolean;
  contentOffsetClass?: string;
  mediaPosition?: string;
  mediaEyebrow?: string;
  mediaTitle?: string;
  mediaDescription?: string;
}>();

const posterFromVideo = computed(() => {
  const src = props.videoSrc || '';
  if (!src) return '';

  const hashIndex = src.indexOf('#');
  const beforeHash = hashIndex >= 0 ? src.slice(0, hashIndex) : src;
  const hash = hashIndex >= 0 ? src.slice(hashIndex) : '';
  const queryIndex = beforeHash.indexOf('?');
  const path = queryIndex >= 0 ? beforeHash.slice(0, queryIndex) : beforeHash;
  const query = queryIndex >= 0 ? beforeHash.slice(queryIndex) : '';

  if (!path.toLowerCase().endsWith('.mp4')) return '';

  return `${path.slice(0, -4)}.poster.jpg${query}${hash}`;
});

const videoPoster = computed(() => {
  return props.posterSrc || posterFromVideo.value;
});

const displayVideoSrc = computed(() => props.videoSrc || '');

defineEmits<{
  (e: 'back'): void
}>();

const goBack = () => {
  const from = window.history.state?.from;
  const fallback = '/';

  if (typeof from === 'string' && from && from !== window.location.href && !from.startsWith('/login') && !from.startsWith('/register') && !from.startsWith('/forgot-password') && !from.startsWith('/reset-password')) {
    void router.push(from);
    return;
  }

  void router.push(fallback);
};

const resetVideoState = () => {
  videoReady.value = false;
  videoErrored.value = false;
};

const requestVideoPlayback = () => {
  const video = videoRef.value;
  if (!video || videoErrored.value) return;

  video.play().catch(() => {
    // Muted autoplay can still be interrupted by the browser; the poster remains underneath.
  });
};

const handleVideoMetadata = () => {
  videoErrored.value = false;
  requestVideoPlayback();
};

const handleVideoReady = () => {
  const video = videoRef.value;
  if (!video || videoErrored.value) return;

  videoErrored.value = false;
  requestVideoPlayback();

  if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA) {
    videoReady.value = true;
  }
};

const handleVideoError = () => {
  videoErrored.value = true;
  videoReady.value = false;
};

watch(
  () => props.videoSrc,
  (src) => {
    resetVideoState();
    if (src) {
      void nextTick(() => {
        const video = videoRef.value;
        if (!video) return;
        video.load();
        requestVideoPlayback();
      });
    }
  },
  { immediate: true },
);
</script>

<template>
  <div class="auth-screen w-full flex flex-col items-center justify-center gap-3">
    <header class="auth-topbar" aria-label="Save Your Finals">
      <div class="auth-brand">
        <span>Save Your Finals</span>
        <i aria-hidden="true"></i>
        <small>题库导入助手</small>
      </div>
      <button class="auth-help-button" type="button" title="帮助">?</button>
    </header>

    <div v-if="$slots.notice" class="pointer-events-none fixed inset-x-0 top-6 z-[9999] flex justify-center px-4">
      <slot name="notice"></slot>
    </div>

    <!-- Card Container -->
    <div class="auth-card w-full max-w-4xl overflow-hidden flex flex-col md:flex-row h-auto md:h-[600px]">
      
      <!-- Left Side: Video/Image -->
      <div class="auth-media-panel hidden md:flex md:w-1/2 relative overflow-hidden items-center justify-center">
        <!-- Back Button (Top Left of Video Section) -->
        <button 
          v-if="props.showBack"
          type="button"
          @click="$emit('back')"
          class="auth-icon-button absolute top-6 left-6 z-20 p-2 transition-all group"
          title="返回上一步"
        >
          <ArrowLeft class="w-6 h-6 transition-transform group-hover:-translate-x-1" />
        </button>

        <div
          v-if="videoPoster && (!videoReady || videoErrored)"
          class="auth-video-poster absolute inset-0 h-full w-full"
          :style="{ '--auth-media-position': props.mediaPosition || 'center' }"
          aria-hidden="true"
        >
          <img
            :src="videoPoster"
            alt=""
            class="h-full w-full object-cover"
          />
        </div>

        <video
          v-if="displayVideoSrc && !videoErrored"
          :key="displayVideoSrc"
          ref="videoRef"
          class="auth-layout-video absolute inset-0 h-full w-full object-cover"
          :class="{ 'is-ready': videoReady }"
          :style="{ '--auth-media-position': props.mediaPosition || 'center' }"
          :poster="videoPoster || undefined"
          autoplay
          muted 
          loop 
          preload="auto"
          playsinline
          webkit-playsinline="true"
          @loadedmetadata="handleVideoMetadata"
          @loadeddata="handleVideoReady"
          @canplay="handleVideoReady"
          @canplaythrough="handleVideoReady"
          @playing="handleVideoReady"
          @progress="handleVideoReady"
          @error="handleVideoError"
        >
          <source :src="displayVideoSrc" type="video/mp4">
        </video>

        <div class="auth-media-shade" aria-hidden="true"></div>
        <div class="auth-media-copy">
          <span>{{ props.mediaEyebrow || "PRECISION WORKFLOW" }}</span>
          <strong>{{ props.mediaTitle || "Master your exams with focused clarity." }}</strong>
          <p>
            {{
              props.mediaDescription ||
              "Seamlessly import, organize, and generate test banks with cinematic precision."
            }}
          </p>
        </div>
      </div>

      <!-- Right Side: Form -->
      <div class="auth-form-panel w-full md:w-1/2 p-7 md:p-12 flex flex-col justify-center relative">
        <!-- Close Button -->
        <button 
          type="button"
          @click="goBack"
          class="auth-icon-button absolute top-6 right-6 z-20 p-2 transition-all"
          aria-label="关闭"
          title="关闭"
        >
          <X class="w-6 h-6" />
        </button>

        <div class="mx-auto w-full max-w-sm" :class="props.contentOffsetClass">
          <div class="auth-heading mb-9 text-center">
            <div class="auth-title mb-2 text-2xl font-bold">
              <slot name="title">Welcome</slot>
            </div>
            <p class="auth-subtitle text-sm">
              <slot name="subtitle"></slot>
            </p>
          </div>
          
          <slot></slot>
        </div>
      </div>

    </div>

    <footer class="auth-footer" aria-label="Legal links">
      <span>© 2026 题库导入助手. CINEMATIC PRECISION.</span>
      <nav>
        <a href="#">隐私政策</a>
        <a href="#">服务条款</a>
        <a href="#">帮助支持</a>
      </nav>
    </footer>
  </div>
</template>

<style scoped>
.auth-layout-video {
  z-index: 1;
  object-position: var(--auth-media-position, center);
  will-change: opacity, transform;
  transform: translateZ(0);
  opacity: 0;
  transition: opacity 280ms ease;
}

.auth-layout-video.is-ready {
  opacity: 1;
}

.auth-video-poster {
  z-index: 0;
}

.auth-video-poster img {
  object-position: var(--auth-media-position, center);
}

</style>
