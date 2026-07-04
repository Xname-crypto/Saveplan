<script setup lang="ts">
import { ArrowLeft, X } from 'lucide-vue-next';
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import { useRouter } from '@/router';

const router = useRouter();
const videoReady = ref(false);
const videoErrored = ref(false);
const resolvedVideoSrc = ref('');
const videoRef = ref<HTMLVideoElement | null>(null);
let bufferTimer: number | undefined;
let videoRequestId = 0;

const props = defineProps<{
  videoSrc?: string;
  posterSrc?: string;
  showBack?: boolean;
  contentOffsetClass?: string;
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

const displayVideoSrc = computed(() => resolvedVideoSrc.value || props.videoSrc || '');

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

const clearBufferTimer = () => {
  if (bufferTimer) {
    window.clearTimeout(bufferTimer);
    bufferTimer = undefined;
  }
};

const resetVideoState = () => {
  clearBufferTimer();
  videoReady.value = false;
  videoErrored.value = false;
  resolvedVideoSrc.value = '';
};

const bufferedAhead = (video: HTMLVideoElement) => {
  try {
    const current = video.currentTime || 0;
    for (let i = 0; i < video.buffered.length; i += 1) {
      if (video.buffered.start(i) <= current && video.buffered.end(i) >= current) {
        return video.buffered.end(i) - current;
      }
    }
  } catch (_e) {
    return 0;
  }

  return 0;
};

const handleVideoReady = () => {
  const video = videoRef.value;
  if (!video || videoErrored.value) return;

  videoErrored.value = false;
  video.play().catch(() => {
    // Muted autoplay can still be interrupted by the browser; the poster remains underneath.
  });

  const duration = Number.isFinite(video.duration) ? video.duration : 0;
  const requiredBuffer = duration > 0 ? Math.min(2.5, Math.max(1.2, duration * 0.12)) : 1.5;

  if (video.readyState >= HTMLMediaElement.HAVE_ENOUGH_DATA || bufferedAhead(video) >= requiredBuffer) {
    clearBufferTimer();
    videoReady.value = true;
    return;
  }

  clearBufferTimer();
  bufferTimer = window.setTimeout(handleVideoReady, 180);
};

const resolveStorageVideo = async (src: string, requestId: number) => {
  const hashIndex = src.indexOf('#');
  const beforeHash = hashIndex >= 0 ? src.slice(0, hashIndex) : src;
  const queryIndex = beforeHash.indexOf('?');
  const path = queryIndex >= 0 ? beforeHash.slice(0, queryIndex) : beforeHash;
  const match = path.match(/^\/video\/([^/]+\.mp4)$/i);

  if (!match) {
    resolvedVideoSrc.value = src;
    return;
  }

  try {
    const response = await fetch(`/api/public/media/auth-video/${encodeURIComponent(match[1])}`);
    if (!response.ok) throw new Error('Failed to resolve auth video');
    const payload = await response.json() as { downloadUrl?: string };
    if (videoRequestId === requestId) {
      resolvedVideoSrc.value = payload.downloadUrl || src;
    }
  } catch (_error) {
    if (videoRequestId === requestId) {
      resolvedVideoSrc.value = src;
    }
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
    const requestId = ++videoRequestId;
    if (src) {
      void resolveStorageVideo(src, requestId);
    }
  },
  { immediate: true },
);
onBeforeUnmount(clearBufferTimer);
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
          v-if="videoPoster"
          class="auth-video-poster absolute inset-0 h-full w-full transition-opacity duration-300"
          :class="videoReady ? 'opacity-0' : 'opacity-100'"
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
          ref="videoRef"
          class="auth-layout-video absolute inset-0 h-full w-full object-cover transition-opacity duration-300"
          :class="videoReady ? 'opacity-100' : 'opacity-0'"
          autoplay
          muted 
          loop 
          preload="auto"
          playsinline
          :poster="videoPoster || undefined"
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
          <span>PRECISION WORKFLOW</span>
          <strong>Master your exams with focused clarity.</strong>
          <p>Seamlessly import, organize, and generate test banks with cinematic precision.</p>
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
          <div class="mb-8 text-center md:text-left">
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
        <a href="#">PRIVACY</a>
        <a href="#">TERMS</a>
        <a href="#">SUPPORT</a>
      </nav>
    </footer>
  </div>
</template>

<style scoped>
.auth-layout-video {
  z-index: 1;
  will-change: opacity, transform;
  transform: translateZ(0);
}

.auth-video-poster {
  z-index: 0;
}
</style>
