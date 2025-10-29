import React from 'react';
import ReactDOM from 'react-dom/client';
import {BrowserRouter} from 'react-router-dom';
import {CssBaseline, ThemeProvider, createTheme} from '@mui/material';
import './index.css';
import App from './App';
import {DevSupport} from "@react-buddy/ide-toolbox";
import {ComponentPreviews, useInitial} from "./dev";

const theme = createTheme({
    palette: {
        mode: 'dark',
        primary: {
            main: '#1DB954', // Spotify green
        },
        background: {
            default: '#121212', // Spotify dark background
            paper: '#282828', // Spotify card background
        },
    },
});

const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
);

root.render(
    <React.StrictMode>
        <BrowserRouter>
            <ThemeProvider theme={theme}>
                <CssBaseline/>
                <DevSupport ComponentPreviews={ComponentPreviews}
                            useInitialHook={useInitial}
                >
                    <App/>
                </DevSupport>
            </ThemeProvider>
        </BrowserRouter>
    </React.StrictMode>
); 