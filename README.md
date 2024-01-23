```bash
$ kustomize version
v5.3.0


# cm config 의 kustomize.buildOptions 는 Shell 에서 허용하는 커멘드만 사용가능하다.
$ kustomize build --help
Build a set of KRM resources using a 'kustomization.yaml' file.
The DIR argument must be a path to a directory containing
'kustomization.yaml', or a git repository URL with a path suffix
specifying same with respect to the repository root.
If DIR is omitted, '.' is assumed.

Usage:
  kustomize build DIR [flags]

Examples:
# Build the current working directory
  kustomize build

# Build some shared configuration directory
  kustomize build /home/config/production

# Build from github
  kustomize build https://github.com/kubernetes-sigs/kustomize.git/examples/helloWorld?ref=v1.0.6


Flags:
      --as-current-user                 use the uid and gid of the command executor to run the function in the container
      --enable-alpha-plugins            enable kustomize plugins
      --enable-exec                     enable support for exec functions (raw executables); do not use for untrusted configs! (Alpha)
      --enable-helm                     Enable use of the Helm chart inflator generator.
      --enable-star                     enable support for starlark functions. (Alpha)
  -e, --env stringArray                 a list of environment variables to be used by functions
      --helm-api-versions stringArray   Kubernetes api versions used by Helm for Capabilities.APIVersions
      --helm-command string             helm command (path to executable) (default "helm")
      --helm-kube-version string        Kubernetes version used by Helm for Capabilities.KubeVersion
  -h, --help                            help for build
      --load-restrictor string          if set to 'LoadRestrictionsNone', local kustomizations may load files from outside their root. This does, however, break the relocatability of the kustomization. (default "LoadRestrictionsRootOnly")
      --mount stringArray               a list of storage options read from the filesystem
      --network                         enable network access for functions that declare it
      --network-name string             the docker network to run the container in (default "bridge")
  -o, --output string                   If specified, write output to this path.

Global Flags:
      --stack-trace   print a stack-trace on error
 
kustomize build --enable-helm --helm-api-versions=networking.k8s.io/v1,apps/v1,v1 > app.yaml
```