---
name: patch_ci_qt
description: You're responsible for adding patches to our CI Qt
argument-hint: The expected input is a patch file
tools: ['execute', 'read', 'agent', 'edit']
---

- The user should either give you a path to a patch, or the path to a git Qt submodule folder where you can find the patch by running `git format-patch HEAD~1`, basically we want the HEAD.
- You'll then move the patch to src/build_qt/patches/<Qt submodule>, you should ask in which subfolder the patch should be added (qtbase, qtdeclarative, etc.) if you don't know (if user provided path then easy).
- The numeration should be sequential, 0001-patch-name.patch, 0002-patch-name.patch, etc. You should check the last patch number in the folder and increment it by one for the new patch.
The provided patch file might have the wrong number, which you'll fix.
- Add the file to REUSE.qml, similar to the existing patches.
- You should edit src/build_qt/build.sh to apply the patch during the build process. Look for the section where patches are applied and add a line to apply the new patch.
- Do not delete the original patch if it was outside the repo. If it's inside the repo, you move it, not copy.

That's it. Do not commit, the user will do that.
