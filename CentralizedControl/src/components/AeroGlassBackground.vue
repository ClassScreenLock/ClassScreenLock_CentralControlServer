<template>
  <canvas ref="canvasRef" class="aero-glass-canvas"></canvas>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as THREE from 'three'

const props = defineProps({
  blurAmount: {
    type: Number,
    default: 20
  },
  opacity: {
    type: Number,
    default: 0.85
  },
  noiseIntensity: {
    type: Number,
    default: 0.03
  },
  refractionStrength: {
    type: Number,
    default: 0.5
  },
  animationSpeed: {
    type: Number,
    default: 0.3
  }
})

const canvasRef = ref(null)
let renderer = null
let scene = null
let camera = null
let material = null
let animationId = null

const vertexShader = `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`

const fragmentShader = `
  uniform sampler2D tDiffuse;
  uniform float time;
  uniform float blurAmount;
  uniform float opacity;
  uniform float noiseIntensity;
  uniform float refractionStrength;
  uniform vec2 resolution;
  varying vec2 vUv;

  // 伪随机函数
  float random(vec2 st) {
    return fract(sin(dot(st.xy, vec2(12.9898, 78.233))) * 43758.5453123);
  }

  // 噪声函数
  float noise(vec2 st) {
    vec2 i = floor(st);
    vec2 f = fract(st);
    float a = random(i);
    float b = random(i + vec2(1.0, 0.0));
    float c = random(i + vec2(0.0, 1.0));
    float d = random(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
  }

  // 高斯模糊
  vec4 gaussianBlur(sampler2D tex, vec2 uv, vec2 resolution, float radius) {
    vec2 pixelSize = 1.0 / resolution;
    vec4 color = vec4(0.0);
    
    float weights[5];
    weights[0] = 0.227027;
    weights[1] = 0.1945946;
    weights[2] = 0.1216216;
    weights[3] = 0.054054;
    weights[4] = 0.016216;
    
    color += texture2D(tex, uv) * weights[0];
    
    for (int i = 1; i < 5; i++) {
      float fi = float(i);
      vec2 offset = pixelSize * radius * fi;
      color += texture2D(tex, uv + offset) * weights[i];
      color += texture2D(tex, uv - offset) * weights[i];
    }
    
    return color;
  }

  void main() {
    vec2 uv = vUv;
    
    // 折射效果 - 模拟玻璃扭曲
    float noiseVal = noise(uv * 10.0 + time * 0.5);
    vec2 refractionOffset = (noiseVal - 0.5) * refractionStrength * 0.01;
    vec2 refractedUv = uv + refractionOffset;
    
    // 动态模糊
    vec4 color = gaussianBlur(tDiffuse, refractedUv, resolution, blurAmount);
    
    // 添加微妙的噪点纹理（模拟玻璃表面）
    float grain = noise(uv * resolution + time * 10.0) * noiseIntensity;
    color.rgb += grain - noiseIntensity * 0.5;
    
    // 边缘光效果 - 模拟光线折射
    float edgeDistance = min(min(uv.x, 1.0 - uv.x), min(uv.y, 1.0 - uv.y));
    float edgeGlow = smoothstep(0.0, 0.15, edgeDistance);
    vec3 edgeColor = vec3(0.6, 0.8, 1.0) * (1.0 - edgeGlow) * 0.15;
    color.rgb += edgeColor;
    
    // 色调映射 - 增强玻璃质感
    color.rgb = pow(color.rgb, vec3(0.95));
    
    // 应用透明度
    color.a = opacity;
    
    gl_FragColor = color;
  }
`

const initWebGL = () => {
  if (!canvasRef.value) return

  const width = canvasRef.value.parentElement?.clientWidth || window.innerWidth
  const height = canvasRef.value.parentElement?.clientHeight || window.innerHeight

  renderer = new THREE.WebGLRenderer({
    canvas: canvasRef.value,
    alpha: true,
    antialias: true
  })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))

  scene = new THREE.Scene()
  camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1)

  const geometry = new THREE.PlaneGeometry(2, 2)

  material = new THREE.ShaderMaterial({
    uniforms: {
      tDiffuse: { value: null },
      time: { value: 0 },
      blurAmount: { value: props.blurAmount },
      opacity: { value: props.opacity },
      noiseIntensity: { value: props.noiseIntensity },
      refractionStrength: { value: props.refractionStrength },
      resolution: { value: new THREE.Vector2(width, height) }
    },
    vertexShader,
    fragmentShader,
    transparent: true
  })

  const mesh = new THREE.Mesh(geometry, material)
  scene.add(mesh)

  // 捕获背景
  captureBackground()
}

const captureBackground = async () => {
  try {
    const canvas = document.createElement('canvas')
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
    const ctx = canvas.getContext('2d')

    // 获取当前页面截图（使用 html2canvas 的简化版本）
    const response = await fetch(`data:image/svg+xml,
      <svg xmlns="http://www.w3.org/2000/svg" width="${canvas.width}" height="${canvas.height}">
        <rect fill="transparent" width="100%" height="100%"/>
      </svg>
    `)
    const blob = await response.blob()
    const img = new Image()
    img.onload = () => {
      ctx.drawImage(img, 0, 0)
      const texture = new THREE.CanvasTexture(canvas)
      texture.minFilter = THREE.LinearFilter
      texture.magFilter = THREE.LinearFilter
      if (material) {
        material.uniforms.tDiffuse.value = texture
      }
    }
    img.src = URL.createObjectURL(blob)
  } catch (error) {
    console.warn('Background capture failed, using fallback:', error)
    // 使用纯色背景作为降级方案
    const canvas = document.createElement('canvas')
    canvas.width = window.innerWidth
    canvas.height = window.innerHeight
    const ctx = canvas.getContext('2d')
    const gradient = ctx.createLinearGradient(0, 0, canvas.width, canvas.height)
    gradient.addColorStop(0, '#0078d4')
    gradient.addColorStop(1, '#005a9e')
    ctx.fillStyle = gradient
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    const texture = new THREE.CanvasTexture(canvas)
    texture.minFilter = THREE.LinearFilter
    texture.magFilter = THREE.LinearFilter
    if (material) {
      material.uniforms.tDiffuse.value = texture
    }
  }
}

const animate = () => {
  animationId = requestAnimationFrame(animate)
  if (material) {
    material.uniforms.time.value += props.animationSpeed * 0.016
    renderer.render(scene, camera)
  }
}

const handleResize = () => {
  if (!canvasRef.value || !renderer) return
  const width = canvasRef.value.parentElement?.clientWidth || window.innerWidth
  const height = canvasRef.value.parentElement?.clientHeight || window.innerHeight
  renderer.setSize(width, height)
  if (material) {
    material.uniforms.resolution.value.set(width, height)
  }
}

onMounted(() => {
  initWebGL()
  animate()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  if (animationId) {
    cancelAnimationFrame(animationId)
  }
  if (renderer) {
    renderer.dispose()
  }
  window.removeEventListener('resize', handleResize)
})

watch(() => props.blurAmount, (val) => {
  if (material) {
    material.uniforms.blurAmount.value = val
  }
})

watch(() => props.opacity, (val) => {
  if (material) {
    material.uniforms.opacity.value = val
  }
})
</script>

<style scoped>
.aero-glass-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}
</style>
