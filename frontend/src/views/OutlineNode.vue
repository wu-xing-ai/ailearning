<template>
  <div class="tree-node">
    <div class="node-header" @click="handleClick">
      <el-icon><Document /></el-icon>
      <span class="node-name">{{ node.title || '未命名' }}</span>
    </div>

    <div class="node-content" v-if="node.children && node.children.length">
      <OutlineNode
        v-for="(c, idx) in node.children"
        :key="idx + '-' + (c.title || idx)"
        :node="c"
        :parentPath="[...parentPath, node.title]"
        @select="$emit('select', $event)"
      />
    </div>
  </div>
</template>

<script setup>
import { Document } from '@element-plus/icons-vue'

const props = defineProps({
  node: { type: Object, required: true },
  parentPath: { type: Array, default: () => [] }
})

const emit = defineEmits(['select'])

const handleClick = () => {
  emit('select', [...props.parentPath, props.node.title])
}
</script>
