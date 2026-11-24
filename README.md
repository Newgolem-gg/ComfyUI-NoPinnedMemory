# ComfyUI-NoPinnedMemory

**Stop ComfyUI's pinned-host-memory cache from eating your RAM — without touching your launch arguments.**

ComfyUI 0.46 introduced *DynamicVRAM*, which keeps a **pinned** (page-locked, `cudaHostRegister`) copy of model weights in host RAM for fast host→GPU transfers. On Windows those pages are reported as **“Shared GPU memory”** in Task Manager — they stay allocated after each image, and the cache is allowed to grow to **40 % of your physical RAM**.

On a 32 GB machine that is ~13 GB of RAM you can watch climb and never come back. This tiny pack turns that cache off at startup.

> **It is not a node.** It registers zero nodes on purpose — it simply runs when ComfyUI imports custom nodes. If you can edit your launch arguments, use the official flag instead:
> ```
> --disable-pinned-memory
> ```
> This pack exists for people who *can't* easily change how ComfyUI is launched (desktop shortcuts, packaged installers, managed launchers).

---

## The symptom

- Task Manager → **“Dedicated GPU memory”** drops back after every image ✅
- **“Shared GPU memory”** keeps growing and never drops ❌
- Eventually the machine starts swapping, or other apps get starved of RAM

That shared block is not VRAM. It is host RAM that was pinned by `cudaHostRegister`, which Windows accounts to the GPU adapter.

## What this does

```python
import comfy.model_management as _mm
_mm.DISABLE_PINNED_MEMORY = True
```

That's it. `comfy/pinned_memory.py` reads the flag **at call time**, so anything loaded after startup skips the registration path.

## Verified against the ComfyUI source

| Location | What it shows |
|---|---|
| `comfy/model_management.py:1631` | `DISABLE_PINNED_MEMORY = args.disable_pinned_memory` |
| `comfy/model_management.py:1632-1634` | forced on for integrated GPUs |
| `comfy/model_management.py:1636-1640` | `MAX_PINNED_MEMORY = ram * 0.40` on Windows |
| `comfy/pinned_memory.py:62` | `get_pin()` returns early when the flag is set → no `cudaHostRegister` |
| `comfy/pinned_memory.py:81` | `pin_memory()` returns immediately when the flag is set |
| `comfy/cli_args.py:207` | `--disable-pinned-memory` argument |

Both consumers look the flag up dynamically (`comfy.model_management.DISABLE_PINNED_MEMORY`), which is why patching the module attribute after import works.

## Install

Copy the folder into `custom_nodes/` and restart ComfyUI:

```
ComfyUI/custom_nodes/ComfyUI-NoPinnedMemory/__init__.py
```

or

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/<your-name>/ComfyUI-NoPinnedMemory.git
```

On startup the console prints:

```
[NoPinnedMemory] 已关闭动态显存的 pinned 主机缓存 (was=False)。...
```

**Uninstall:** delete the folder and restart. There is no state to clean up.

## Cost

Model weights are transferred through pageable memory instead of pinned memory, so **dynamic layer loading / offloading is slower** — typically tens of seconds per image on a machine that is already offloading, while the inference itself takes minutes. VRAM usage is unchanged; only host RAM behaviour changes.

If your ComfyUI **never offloads** (model fits in VRAM comfortably), you will barely notice the difference.

## When not to use it

- ComfyUI older than the DynamicVRAM change has no pinned-memory cache at all — the pack detects this and logs that it is unnecessary.
- If you have plenty of RAM and load/unload models constantly, the pinned cache is a genuine speed win; don't disable it.
- If you *can* pass launch arguments, `--disable-pinned-memory` is equivalent and needs no custom node.

## Compatibility

Tested on ComfyUI 0.46.x, Windows 11, RTX 3090. The flag is looked up with `hasattr`, so on versions without the DynamicVRAM mechanism the pack logs a warning and changes nothing instead of pretending to work.

## License

MIT — see [LICENSE](LICENSE).

---

# 中文说明

**关掉 ComfyUI 的 pinned 主机内存缓存，且不必改启动参数。**

ComfyUI 0.46 的 *DynamicVRAM* 会在主机内存里保留一份**被 pin 住**（页锁定，`cudaHostRegister`）的模型权重副本，用于加速 主机→显存 传输。Windows 会把这块内存统计成任务管理器里的 **“共享 GPU 内存”**——每张图跑完后它不会回落，而且上限是**物理内存的 40%**。32G 机器上就是约 13 GB，只涨不降。

> **这不是一个节点**。它故意不注册任何节点，只是在 ComfyUI 加载自定义节点时执行一次。如果你能改启动参数，直接用官方开关 `--disable-pinned-memory` 效果完全相同，不需要装这个。

## 现象判断

- 任务管理器里「专用 GPU 内存」每张图结束会回落 ✅
- 「共享 GPU 内存」一路上涨、不释放 ❌ → 这就是被 pin 住的主机内存

## 原理

```python
import comfy.model_management as _mm
_mm.DISABLE_PINNED_MEMORY = True
```

`comfy/pinned_memory.py` 是在**调用时**才读这个标志的，所以启动后改模块属性对后续所有模型加载都生效。

## 代价

模型权重改走可分页内存，**动态换层/卸载会变慢**（已经是靠 offload 跑的场景，每张图可能多十几秒；推理本身是分钟级）。显存占用不变，只影响主机内存行为。如果你的模型本来就放得下显存、跑的时候不换层，基本感觉不到差别。

## 何时不该用

- 老版本 ComfyUI 根本没有这个缓存机制——本插件会检测并提示无需安装。
- 内存充足、模型频繁加载卸载时，pinned 缓存其实是提速手段，别关。
- 能改启动参数就用 `--disable-pinned-memory`，不必装自定义节点。

## 安装 / 卸载

放进 `ComfyUI/custom_nodes/ComfyUI-NoPinnedMemory/`，重启。卸载就是删掉文件夹再重启，没有残留状态。
