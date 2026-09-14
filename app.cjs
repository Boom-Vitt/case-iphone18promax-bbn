// Explicit hosting entry point, including hosts that load the app with require().
import('./server/app.mjs').then(({ startApp }) => startApp()).catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});
