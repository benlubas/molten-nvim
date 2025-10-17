# Concurrent Cell Execution Implementation

## Overview

This document describes the implementation of concurrent cell execution support in Molten via Jupyter message ID tracking.

## Problem Statement

Previously, Molten used a single-output queue model where:
- `runtime.run_code()` ignored the `msg_id` returned by Jupyter's `execute()` call
- `runtime.tick()` routed ALL messages to `self.current_output` without filtering
- This caused outputs to appear in wrong cells when multiple cells executed concurrently

## Solution

Implemented proper Jupyter message ID tracking to route outputs to the correct cells based on the `parent_header["msg_id"]` field in Jupyter protocol messages.

## Changes Made

### 1. `runtime.py` Changes

#### Added Instance Variable
```python
active_executions: Dict[str, Output]  # msg_id -> Output mapping
```

#### Modified `__init__`
Added initialization:
```python
self.active_executions = {}
```

#### Modified `run_code()`
**Before:**
```python
def run_code(self, code: str) -> None:
    self.kernel_client.execute(code)
```

**After:**
```python
def run_code(self, code: str) -> str:
    """Execute code and return the msg_id for tracking"""
    msg_id = self.kernel_client.execute(code)
    return msg_id
```

#### Added `register_execution()` Method
```python
def register_execution(self, msg_id: str, output: Output) -> None:
    """Register a msg_id with its output destination for concurrent execution"""
    self.active_executions[msg_id] = output
```

#### Modified `tick()` Method
**Key changes:**
1. Maintains backwards compatibility - if `output` parameter is provided, uses legacy single-output mode
2. When `output=None`, enables new concurrent mode:
   - Routes messages by checking `parent_header["msg_id"]`
   - Looks up target output from `self.active_executions` mapping
   - Automatically cleans up completed executions

**New concurrent execution logic:**
```python
# Route message to correct output based on parent_header
parent_header = message.get("parent_header", {})
msg_id = parent_header.get("msg_id")

if msg_id not in self.active_executions:
    # Message from unknown execution - skip it
    continue

target_output = self.active_executions[msg_id]
did_stuff_now = self._tick_one(target_output, message["msg_type"], message["content"])

# Clean up completed executions
if target_output.status == OutputStatus.DONE:
    del self.active_executions[msg_id]
```

### 2. `moltenbuffer.py` Changes

#### Added Instance Variable
```python
execution_msg_ids: Dict[CodeCell, str]  # cell -> msg_id mapping
```

#### Modified `__init__`
Added initialization:
```python
self.execution_msg_ids = {}
```

#### Modified `run_code()`
**Key changes:**
1. Captures `msg_id` returned from `runtime.run_code()`
2. Registers the msg_id with runtime for output routing
3. Stores msg_id in local tracking dict

```python
# Capture msg_id from execution for tracking
msg_id = self.runtime.run_code(code)

self.outputs[span] = OutputBuffer(...)

# Register the msg_id with runtime for concurrent execution routing
self.runtime.register_execution(msg_id, self.outputs[span].output)
self.execution_msg_ids[span] = msg_id
```

#### Modified `tick()`
**Key changes:**
1. Checks if `execution_msg_ids` is non-empty to determine concurrent mode
2. In concurrent mode:
   - Calls `runtime.tick(None)` to enable msg_id routing
   - Iterates through tracked cells to check completion
   - Cleans up completed msg_ids
3. Falls back to legacy single-output mode if no tracked msg_ids

```python
# Use concurrent execution mode if we have tracked msg_ids
if self.execution_msg_ids:
    # Let runtime handle routing by msg_id
    did_stuff = self.runtime.tick(None)

    # Check which cells completed and clean up
    for span, msg_id in list(self.execution_msg_ids.items()):
        if span not in self.outputs:
            del self.execution_msg_ids[span]
            continue

        output = self.outputs[span].output

        if output.status == OutputStatus.DONE:
            # Clean up completed execution
            del self.execution_msg_ids[span]
            # ... handle auto-open features ...
```

#### Modified `_delete_cell()`
Added cleanup of msg_id tracking:
```python
# Clean up msg_id tracking if this cell was being tracked
if cell in self.execution_msg_ids:
    del self.execution_msg_ids[cell]
```

## Backwards Compatibility

The implementation maintains full backwards compatibility:
- External API unchanged (commands, autocommands, etc.)
- Legacy single-output mode still works when `runtime.tick(output)` is called with an output
- Existing Output and OutputBuffer classes unchanged
- Only internal routing logic modified

## Testing Strategy

1. **Single cell execution**: Verify existing behavior still works
2. **Sequential execution**: Test running cells one after another
3. **Concurrent execution**: Test running multiple cells rapidly (primary improvement)
4. **Error handling**: Test errors appearing in correct cells
5. **Restart scenarios**: Test interrupt and restart with multiple active cells
6. **Cell deletion**: Test deleting cells with active executions

## Benefits

1. **True concurrent execution**: Multiple cells can now execute simultaneously with outputs routed correctly
2. **No artificial delays**: Removes need for time-based delays between cell submissions
3. **Proper message routing**: Each cell receives only its own outputs based on Jupyter protocol
4. **Scalable**: Can handle many concurrent cells without queue management complexity

## Next Steps

1. Test the implementation with real notebooks
2. Verify no regressions in single-cell execution
3. Test edge cases (errors, interrupts, restarts)
4. Consider removing `queued_outputs` and `current_output` in future major version (no longer needed with msg_id tracking)
5. Create pull request to upstream repository
