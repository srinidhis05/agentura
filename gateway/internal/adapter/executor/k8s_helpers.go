package executor

import (
	"bytes"
	"context"
	"io"
	"os/exec"
)

// execCommand wraps os/exec.CommandContext for testability.
var execCommand = func(ctx context.Context, name string, args ...string) *exec.Cmd {
	return exec.CommandContext(ctx, name, args...)
}

// bytesReader wraps bytes.NewReader for use in cmd.Stdin.
func bytesReader(data []byte) io.Reader {
	return bytes.NewReader(data)
}
