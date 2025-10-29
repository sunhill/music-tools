import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const Navbar = () => {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Spotify Export
        </Typography>
        <Box>
          <Button
            color="inherit"
            component={RouterLink}
            to="/artists"
            sx={{ mx: 1 }}
          >
            Artists
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/albums"
            sx={{ mx: 1 }}
          >
            Albums
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/tracks"
            sx={{ mx: 1 }}
          >
            Tracks
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/playlists"
            sx={{ mx: 1 }}
          >
            Playlists
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar; 