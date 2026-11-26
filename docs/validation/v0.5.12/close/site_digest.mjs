// Read-only: print the site's editorial digest (lib/editorial.ts, editorialDigest) of the working copy
// C:/Projetos/refute-site, for the approval of #218 comment 7202817195, item 2. It uses the site's own
// code and installed packages (Node runs the .ts files by type stripping); it writes nothing.
import { pathToFileURL } from 'node:url';

const root = 'C:/Projetos/refute-site';
const { editorialDigest, editorialApproval } = await import(pathToFileURL(`${root}/lib/editorial.ts`).href);
const digest = editorialDigest(root);
const state = editorialApproval(root).state;
console.log(JSON.stringify({ digest, state }));
