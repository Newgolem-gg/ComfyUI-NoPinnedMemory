# -*- coding: utf-8 -*-
"""
ComfyUI-NoPinnedMemory
======================

作用：关闭 ComfyUI 0.46 “动态显存（DynamicVRAM）”在主机内存里为模型权重做的
pinned（cudaHostRegister）缓存。

现象：任务管理器里“专用 GPU 内存”每张图结束都会回落，但“共享 GPU 内存”
      一直很高、甚至一路上涨不释放 —— 那部分就是被 pin 住的模型权重副本
      （Windows 会把 cudaHostRegister 的主机内存算进“共享 GPU 内存”），
      上限是物理内存的 40%，只在系统内存快耗尽时才回收。

代价：模型权重从主机到显存改成走可分页内存，动态加载/换层会慢一些
      （每张图多十几秒量级，而推理本身是分钟级）。

还原：删掉整个 ComfyUI-NoPinnedMemory 文件夹，重启 ComfyUI 即可。

说明：这不是一个可用节点，只是利用“自定义节点在 ComfyUI 启动时加载”这一时机，
      设置官方开关 `--disable-pinned-memory` 对应的运行时标志。
      如果你能直接改启动参数，加 `--disable-pinned-memory` 效果完全相同，
      那时就不需要这个文件夹了。
"""

import logging

LOGGER = logging.getLogger("NoPinnedMemory")

try:
    import comfy.model_management as _mm

    # 旧版 ComfyUI 没有 DynamicVRAM/pinned memory，直接赋值只会凭空造出一个
    # 没人读取的属性，日志却会说“已关闭”。这里先确认标志确实存在。
    if not hasattr(_mm, "DISABLE_PINNED_MEMORY"):
        LOGGER.warning(
            "[NoPinnedMemory] 当前 ComfyUI 没有 DISABLE_PINNED_MEMORY 标志"
            "（旧版本没有 DynamicVRAM pinned memory），本插件无需安装，已跳过。"
        )
    else:
        was = _mm.DISABLE_PINNED_MEMORY
        _mm.DISABLE_PINNED_MEMORY = True
        LOGGER.warning(
            "[NoPinnedMemory] 已关闭动态显存的 pinned 主机缓存 (was=%s)。"
            "模型改用可分页内存，'共享 GPU 内存' 不会再涨到内存的 40%%。"
            "删除 custom_nodes/ComfyUI-NoPinnedMemory 可还原。",
            was,
        )
except Exception as exc:  # 不允许因为这里出错而影响 ComfyUI 启动
    LOGGER.warning("[NoPinnedMemory] 设置失败：%s: %s", type(exc).__name__, exc)

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}
