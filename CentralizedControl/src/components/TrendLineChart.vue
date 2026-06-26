<template>
  <div class="trend-chart-wrapper card">
    <div class="chart-header">
      <h2 class="section-title">
        <span class="title-glow"></span>
        活动趋势
      </h2>
      <div class="chart-tabs">
        <button
          v-for="tab in rangeTabs"
          :key="tab.key"
          :class="['tab-btn', { active: activeRange === tab.key }]"
          @click="activeRange = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>
    </div>
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  trendData: {
    type: Array,
    default: () => []
  },
  actionTypeData: {
    type: Array,
    default: () => []
  }
})

const chartRef = ref(null)
let chartInstance = null
const activeRange = ref('trend')
const rangeTabs = [
  { key: 'trend', label: '每日趋势' },
  { key: 'actions', label: '操作分类' }
]

const colors = ['#6366f1', '#8b5cf6', '#a78bfa', '#c084fc', '#e879f9', '#f0abfc']

const getChartOption = () => {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark'
  const textColor = isDark ? '#e0e0e0' : '#555'
  const axisColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)'
  const gridColor = isDark ? 'rgba(255,255,255,0.04)' : 'rgba(0,0,0,0.04)'

  if (activeRange.value === 'trend') {
    const categories = props.trendData.map(d => d.label)
    const values = props.trendData.map(d => d.value)
    const dates = props.trendData.map(d => d.date || '')

    return {
      animation: true,
      animationDuration: 800,
      animationEasing: 'cubicOut',
      tooltip: {
        trigger: 'axis',
        backgroundColor: isDark ? 'rgba(30,30,30,0.9)' : 'rgba(255,255,255,0.9)',
        borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
        borderWidth: 1,
        backdropFilter: 'blur(12px)',
        textStyle: {
          color: textColor,
          fontSize: 13
        },
        formatter: function (params) {
          const item = params[0]
          if (!item) return ''
          const dateStr = dates[item.dataIndex] || ''
          const dateInfo = dateStr ? `<div style="font-size:12px;color:${textColor};opacity:0.7;margin-bottom:4px">${dateStr}</div>` : ''
          return `
            <div style="font-weight:600;margin-bottom:6px">${item.axisValue}</div>
            ${dateInfo}
            <div style="display:flex;align-items:center;gap:8px">
              <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${item.color}"></span>
              <span>活动次数</span>
              <span style="font-weight:700;font-size:16px;margin-left:auto">${item.value}</span>
            </div>
          `
        },
        extraCssText: 'border-radius:12px;padding:12px 16px;box-shadow:0 8px 32px rgba(0,0,0,0.2)'
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '8%',
        top: '8%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: categories,
        axisLine: { lineStyle: { color: axisColor } },
        axisTick: { show: false },
        axisLabel: {
          color: textColor,
          fontSize: 12,
          fontWeight: 500
        },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        splitLine: {
          lineStyle: {
            color: gridColor,
            type: 'dashed'
          }
        },
        axisLabel: {
          color: textColor,
          fontSize: 11
        },
        axisLine: { show: false },
        axisTick: { show: false }
      },
      series: [
        {
          type: 'line',
          data: values,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          showSymbol: true,
          animation: true,
          animationDuration: 800,
          animationEasing: 'cubicOut',
          lineStyle: {
            width: 3,
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 1, y2: 0,
              colorStops: [
                { offset: 0, color: '#6366f1' },
                { offset: 1, color: '#8b5cf6' }
              ]
            }
          },
          itemStyle: {
            color: '#6366f1',
            borderColor: isDark ? '#1a1a2e' : '#fff',
            borderWidth: 2
          },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(99,102,241,0.35)' },
                { offset: 0.5, color: 'rgba(99,102,241,0.12)' },
                { offset: 1, color: 'rgba(99,102,241,0.02)' }
              ]
            }
          },
          markLine: values.length > 0 ? {
            silent: true,
            symbol: 'none',
            data: [
              {
                yAxis: Math.round(values.reduce((a, b) => a + b, 0) / values.length),
                label: {
                  formatter: '均值 {c}',
                  position: 'start',
                  color: textColor,
                  fontSize: 11,
                  opacity: 0.6
                },
                lineStyle: {
                  color: gridColor,
                  type: 'dashed',
                  width: 1
                }
              }
            ]
          } : undefined
        }
      ]
    }
  } else {
    const data = props.actionTypeData.map((d, i) => ({
      name: d.label,
      value: d.value,
      itemStyle: {
        color: colors[i % colors.length],
        borderRadius: 4
      }
    }))
    const total = data.reduce((s, d) => s + d.value, 0)

    return {
      animation: true,
      animationDuration: 800,
      animationEasing: 'cubicOut',
      tooltip: {
        trigger: 'item',
        backgroundColor: isDark ? 'rgba(30,30,30,0.9)' : 'rgba(255,255,255,0.9)',
        borderColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)',
        borderWidth: 1,
        textStyle: { color: textColor, fontSize: 13 },
        formatter: function (params) {
          const pct = total > 0 ? params.percent : 0
          return `
            <div style="font-weight:600;margin-bottom:6px">${params.name}</div>
            <div style="display:flex;align-items:center;gap:8px">
              <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${params.color}"></span>
              <span>${params.value} 次</span>
              <span style="font-weight:600;margin-left:auto;color:${textColor}">${pct.toFixed(1)}%</span>
            </div>
          `
        },
        extraCssText: 'border-radius:12px;padding:12px 16px;box-shadow:0 8px 32px rgba(0,0,0,0.2)'
      },
      series: [
        {
          type: 'pie',
          radius: ['38%', '68%'],
          center: ['50%', '50%'],
          avoidLabelOverlap: true,
          padAngle: 2,
          itemStyle: {
            borderRadius: 6,
            borderColor: isDark ? 'rgba(30,30,30,0.9)' : 'rgba(255,255,255,0.9)',
            borderWidth: 2
          },
          label: {
            show: true,
            formatter: function (params) {
              return `{name|${params.name}}\n{value|${params.value}}`
            },
            rich: {
              name: {
                fontSize: 13,
                fontWeight: 600,
                color: textColor,
                lineHeight: 22
              },
              value: {
                fontSize: 11,
                color: textColor,
                opacity: 0.6,
                lineHeight: 16
              }
            }
          },
          labelLine: {
            lineStyle: {
              color: axisColor
            }
          },
          emphasis: {
            itemStyle: {
              shadowBlur: 12,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0,0,0,0.3)'
            },
            label: {
              fontSize: 14,
              fontWeight: 700
            }
          },
          animation: true,
          animationDuration: 1000,
          animationEasing: 'cubicOut',
          data: data.length > 0 ? data : [{ name: '暂无数据', value: 1, itemStyle: { color: gridColor } }]
        }
      ]
    }
  }
}

const renderChart = () => {
  if (!chartRef.value) return
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value, null, { renderer: 'canvas' })
  }
  chartInstance.setOption(getChartOption(), true)
  chartInstance.resize()
}

const handleResize = () => {
  chartInstance?.resize()
}

watch(() => [props.trendData, props.actionTypeData], () => {
  nextTick(renderChart)
}, { deep: true })

watch(activeRange, () => {
  nextTick(renderChart)
})

onMounted(() => {
  nextTick(() => {
    renderChart()
    window.addEventListener('resize', handleResize)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.trend-chart-wrapper {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: var(--fui-radius);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 24px;
  position: relative;
  overflow: hidden;
}

.trend-chart-wrapper::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(255, 255, 255, 0.3),
    transparent
  );
  animation: shimmer 3s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.section-title {
  font-size: 1.5em;
  font-weight: 700;
  color: var(--fui-text);
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
}

.title-glow {
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.2));
  border-radius: 50%;
  animation: titleGlow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.5);
}

@keyframes titleGlow {
  0%, 100% {
    transform: scale(1);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.3);
    opacity: 1;
    box-shadow: 0 0 20px rgba(255, 255, 255, 0.8);
  }
}

.chart-tabs {
  display: flex;
  gap: 4px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 8px;
  padding: 3px;
}

.tab-btn {
  padding: 6px 16px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--fui-text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.tab-btn:hover {
  color: var(--fui-text);
  background: rgba(255, 255, 255, 0.08);
}

.tab-btn.active {
  color: #fff;
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.chart-container {
  width: 100%;
  height: 320px;
}

@media (max-width: 768px) {
  .chart-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .chart-container {
    height: 260px;
  }
}
</style>
