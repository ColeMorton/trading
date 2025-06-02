import type { CodegenConfig } from '@graphql-codegen/cli';

const config: CodegenConfig = {
  overwrite: true,
  schema: 'http://localhost:8000/graphql',
  documents: 'src/**/*.{ts,tsx,graphql,gql}',
  generates: {
    'src/graphql/generated.ts': {
      plugins: [
        'typescript',
        'typescript-operations',
        'typescript-react-apollo'
      ],
      config: {
        withHooks: true,
        withResultType: true,
        withRefetchFn: true,
        avoidOptionals: false,
        skipTypename: false,
        enumsAsTypes: false,
        dedupeFragments: true,
        pureMagicComment: true,
        strictScalars: true,
        scalars: {
          DateTime: 'string',
          JSON: 'Record<string, any>',
          ID: 'string'
        }
      }
    }
  }
};

export default config;