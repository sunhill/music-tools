import React, {useEffect, useState} from 'react';
import {Route, Routes, useLocation, useNavigate} from 'react-router-dom';
import {
    Alert,
    Box,
    Card,
    CardContent,
    CardMedia,
    CircularProgress,
    Container,
    FormControl,
    Grid,
    IconButton,
    MenuItem,
    Pagination,
    Select,
    SelectChangeEvent,
    Tooltip,
    Typography,
    Button
} from '@mui/material';
import Navbar from './components/Navbar';
import SortIcon from '@mui/icons-material/Sort';
import CreatePlaylist from './components/CreatePlaylist';
import SearchFilter from './components/SearchFilter';
import ViewToggle from './components/ViewToggle';
import ListView from './components/ListView';
import {Artist, Album, Track, Playlist, SpotifyImage} from './types';
import {ArrowUpward, ArrowDownward, GridView, List} from '@mui/icons-material';

interface PaginationProps {
    total: number;
    page: number;
    pageSize: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (pageSize: number) => void;
}

const ITEMS_PER_PAGE_OPTIONS = [12, 24, 48, 96, 144, 192, 240];

const getLargestImage = (images: SpotifyImage[]): string => {
    if (!images || images.length === 0) return 'https://via.placeholder.com/300';
    return images.reduce((largest, current) =>
        current.height > largest.height ? current : largest
    ).url;
};

const formatDuration = (ms: number): string => {
    const minutes = Math.floor(ms / 60000);
    const seconds = Math.floor((ms % 60000) / 1000);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

const PaginationComponent = ({total, page, pageSize, onPageChange, onPageSizeChange}: PaginationProps) => {
    const navigate = useNavigate();
    const location = useLocation();

    const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
        const params = new URLSearchParams(location.search);
        params.set('page', value.toString());
        params.set('limit', pageSize.toString());
        navigate(`${location.pathname}?${params.toString()}`);
    };

    const handlePageSizeChange = (event: SelectChangeEvent<number>) => {
        const newPageSize = Number(event.target.value);
        onPageSizeChange(newPageSize);
        const params = new URLSearchParams(location.search);
        params.set('limit', newPageSize.toString());
        params.set('page', '1'); // Reset to first page when changing page size
        navigate(`${location.pathname}?${params.toString()}`);
    };

    return (
        <Box sx={{display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 2, mt: 4}}>
            <FormControl size="small">
                <Select
                    value={pageSize}
                    onChange={handlePageSizeChange}
                    sx={{minWidth: 100}}
                >
                    {ITEMS_PER_PAGE_OPTIONS.map((size) => (
                        <MenuItem key={size} value={size}>
                            {size} per page
                        </MenuItem>
                    ))}
                </Select>
            </FormControl>
            <Pagination
                count={Math.ceil(total / pageSize)}
                page={page}
                onChange={handlePageChange}
                color="primary"
                size="large"
            />
        </Box>
    );
};

interface SortablePageTitleProps {
    title: string;
    sortOrder: 'asc' | 'desc' | null;
    onSort: () => void;
    view: 'grid' | 'list';
    onViewChange: (view: 'grid' | 'list') => void;
}

const SortablePageTitle: React.FC<SortablePageTitleProps> = ({
                                                                 title,
                                                                 sortOrder,
                                                                 onSort,
                                                                 view,
                                                                 onViewChange
                                                             }) => (
    <Box sx={{display: 'flex', alignItems: 'center', gap: 2, mb: 3}}>
        <Typography variant="h4" component="h1">
            {title}
        </Typography>
        <IconButton onClick={onSort} size="small">
            {sortOrder === 'asc' ? <ArrowUpward/> : <ArrowDownward/>}
        </IconButton>
        <IconButton onClick={() => onViewChange(view === 'grid' ? 'list' : 'grid')} size="small">
            {view === 'grid' ? <GridView/> : <List/>}
        </IconButton>
    </Box>
);

const ArtistsPage = () => {
    const [artists, setArtists] = useState<Artist[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [total, setTotal] = useState(0);
    const [totalFiltered, setTotalFiltered] = useState<number | null>(null);
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(12);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc' | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [genreFilter, setGenreFilter] = useState('');
    const [view, setView] = useState<'grid' | 'list'>('grid');
    const location = useLocation();
    const navigate = useNavigate();

    // Inside ArtistsPage component

    const [allGenres, setAllGenres] = useState<{ value: string, label: string }[]>([]);

    useEffect(() => {
        const fetchGenres = async () => {
            try {
                const response = await fetch('http://localhost:8001/genres');
                if (!response.ok) throw new Error('Failed to fetch genres');
                const data = await response.json();
                setAllGenres(data.genres.map((genre: string) => ({ value: genre, label: genre })));
            } catch (err) {
                // Optionally handle error
                setAllGenres([]);
            }
        };
        fetchGenres();
    }, []);

    const fetchArtists = async () => {
        try {
            setLoading(true);
            const response = await fetch(
                `http://localhost:8001/artists?page=${page}&limit=${pageSize}${sortOrder ? `&sort=${sortOrder}` : ''}${searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''}${genreFilter ? `&genre=${encodeURIComponent(genreFilter)}` : ''}`
            );
            if (!response.ok) {
                throw new Error('Failed to fetch artists');
            }
            const data = await response.json();
            setArtists(data.artists);
            setTotal(data.total);
            setTotalFiltered(data.total_filtered || null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch artists');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const pageParam = parseInt(params.get('page') || '1');
        const limitParam = parseInt(params.get('limit') || '12');
        const sortParam = params.get('sort') as 'asc' | 'desc' | null;
        const searchParam = params.get('search') || '';
        const genreParam = params.get('genre') || '';
        setPage(pageParam);
        setPageSize(limitParam);
        setSortOrder(sortParam);
        setSearchQuery(searchParam);
        setGenreFilter(genreParam);
    }, [location]);

    useEffect(() => {
        fetchArtists();
    }, [page, pageSize, sortOrder, searchQuery, genreFilter]);

    const genreOptions= allGenres;

    const handleSort = () => {
        const newSortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
        setSortOrder(newSortOrder);
        // Update URL parameters
        const params = new URLSearchParams(location.search);
        params.set('sort', newSortOrder);
        navigate(`${location.pathname}?${params.toString()}`);
    };

    const handleSearch = (query: string) => {
        setSearchQuery(query);
        const params = new URLSearchParams(location.search);
        params.set('search', query);
        params.set('page', '1'); // Reset to first page on filter
        navigate(`${location.pathname}?${params.toString()}`);
    };

    const handleGenreFilter = (genre: string) => {
        setGenreFilter(genre);
        const params = new URLSearchParams(location.search);
        params.set('genre', genre);
        params.set('page', '1');
        navigate(`${location.pathname}?${params.toString()}`);
    };

    if (loading) return <CircularProgress/>;
    if (error) return <Alert severity="error">{error}</Alert>;

    return (
        <Container>
            <SortablePageTitle
                title="Artists"
                sortOrder={sortOrder}
                onSort={handleSort}
                view={view}
                onViewChange={setView}
            />
            <SearchFilter
                onSearch={handleSearch}
                onFilterChange={handleGenreFilter}
                filterOptions={genreOptions}
                placeholder="Search artists..."
            />
            <Typography variant="subtitle2" sx={{mb: 2}}>
                {searchQuery ? `Search: ${searchQuery}` : ''}
            </Typography>
            <PaginationComponent
                total={total}
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
            />
            <Typography variant="subtitle1" sx={{mb: 2}}>
                {totalFiltered} item{total !== 1 ? 's' : ''} found
                {typeof totalFiltered === 'number' && total !== totalFiltered
                    ? ` (filtered from ${total})`
                    : ''}
            </Typography>
            {view === 'grid' ? (
                <Grid container spacing={3}>
                    {artists.map((artist) => (
                        <Grid item xs={12} sm={6} md={4} key={artist.id}>
                            <Card sx={{height: '100%', display: 'flex', flexDirection: 'column'}}>
                                <CardMedia
                                    component="img"
                                    height="200"
                                    image={getLargestImage(artist.images)}
                                    alt={artist.name}
                                />
                                <CardContent sx={{flexGrow: 1}}>
                                    <Typography gutterBottom variant="h5" component="h2">
                                        {artist.name}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {artist.genres.join(', ')}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {artist.followers.total.toLocaleString()} followers
                                    </Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            ) : (
                <ListView
                    items={artists}
                    type="artists"
                    getLargestImage={getLargestImage}
                />
            )}
            <PaginationComponent
                total={total}
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
            />
        </Container>
    );
};

const AlbumsPage = () => {
    const [albums, setAlbums] = useState<Album[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [total, setTotal] = useState(0);
    const [totalFiltered, setTotalFiltered] = useState<number | null>(null);
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(12);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc' | null>(null);
    const [sortField, setSortField] = useState<'name' | 'artist' | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [albumTypeFilter, setAlbumTypeFilter] = useState('');
    const [view, setView] = useState<'grid' | 'list'>('grid');
    const location = useLocation();
    const navigate = useNavigate();

    const fetchAlbums = async () => {
        try {
            setLoading(true);
            const response = await fetch(
                `http://localhost:8001/albums?page=${page}&limit=${pageSize}${sortOrder ? `&sort=${sortOrder}` : ''}${sortField ? `&field=${sortField}` : ''}${searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''}${albumTypeFilter ? `&type=${encodeURIComponent(albumTypeFilter)}` : ''}`
            );
            if (!response.ok) {
                throw new Error('Failed to fetch albums');
            }
            const data = await response.json();
            setAlbums(data.albums);
            setTotal(data.total);
            setTotalFiltered(data.total_filtered || null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch albums');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const pageParam = parseInt(params.get('page') || '1');
        const limitParam = parseInt(params.get('limit') || '12');
        const sortParam = params.get('sort') as 'asc' | 'desc' | null;
        const sortFieldParam = params.get('sort_field') as 'name' | 'artist' | null;
        const searchParam = params.get('search') || '';
        const typeParam = params.get('type') || '';
        setPage(pageParam);
        setPageSize(limitParam);
        setSortOrder(sortParam);
        setSortField(sortFieldParam);
        setSearchQuery(searchParam);
        setAlbumTypeFilter(typeParam);
    }, [location]);

    useEffect(() => {
        fetchAlbums();
    }, [page, pageSize, sortOrder, sortField, searchQuery, albumTypeFilter]);

    // Album type options for filter
    const albumTypeOptions = [
        {value: 'album', label: 'Album'},
        {value: 'single', label: 'Single'},
        {value: 'compilation', label: 'Compilation'}
    ];

    const handleSort = () => {
        const newSortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
        setSortOrder(newSortOrder);
        // Update URL parameters
        const params = new URLSearchParams(location.search);
        params.set('sort', newSortOrder);
        navigate(`${location.pathname}?${params.toString()}`);
    };

    const handleSortFieldChange = (field: 'name' | 'artist') => {
        setSortField(field);
        // Reset to first page when changing sort field
        setPage(1);
        const params = new URLSearchParams(location.search);
        params.set('sort_field', field);
        params.set('page', '1');
        navigate(`${location.pathname}?${params.toString()}`);
    };

    const handleSearch = (query: string) => {
        setSearchQuery(query);
        const params = new URLSearchParams(location.search);
        params.set('search', query);
        params.set('page', '1'); // Reset to first page on filter
        navigate(`${location.pathname}?${params.toString()}`);
    };

    const handleAlbumTypeFilter = (albumType: string) => {
        setAlbumTypeFilter(albumType);
        const params = new URLSearchParams(location.search);
        params.set('type', albumType);
        params.set('page', '1');
        navigate(`${location.pathname}?${params.toString()}`);
    };




    if (loading) return <CircularProgress/>;
    if (error) return <Alert severity="error">{error}</Alert>;

    return (
        <Container>
            <Box sx={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3}}>
                <SortablePageTitle
                    title="Albums"
                    sortOrder={sortOrder}
                    onSort={handleSort}
                    view={view}
                    onViewChange={setView}
                />
                <Box sx={{display: 'flex', gap: 1}}>
                    <Button
                        variant={sortField === 'name' ? 'contained' : 'outlined'}
                        size="small"
                        onClick={() => handleSortFieldChange('name')}
                    >
                        Name
                    </Button>
                    <Button
                        variant={sortField === 'artist' ? 'contained' : 'outlined'}
                        size="small"
                        onClick={() => handleSortFieldChange('artist')}
                    >
                        Artist
                    </Button>
                </Box>
            </Box>
            <SearchFilter
                onSearch={handleSearch}
                onFilterChange={handleAlbumTypeFilter}
                filterOptions={albumTypeOptions}
                placeholder="Search albums..."
            />
            <Typography variant="subtitle2" sx={{mb: 2}}>
                {searchQuery ? `Search: ${searchQuery}` : ''}
            </Typography>
            <PaginationComponent
                total={total}
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
            />
            <Typography variant="subtitle1" sx={{mb: 2}}>
                {totalFiltered} item{total !== 1 ? 's' : ''} found
                {typeof totalFiltered === 'number' && total !== totalFiltered
                    ? ` (filtered from ${total})`
                    : ''}
            </Typography>
            {view === 'grid' ? (
                <Grid container spacing={3}>
                    {albums.map((album) => (
                        <Grid item xs={12} sm={6} md={4} key={album.id}>
                            <Card sx={{height: '100%', display: 'flex', flexDirection: 'column'}}>
                                <CardMedia
                                    component="img"
                                    height="200"
                                    image={getLargestImage(album.images)}
                                    alt={album.name}
                                />
                                <CardContent sx={{flexGrow: 1}}>
                                    <Typography gutterBottom variant="h5" component="h2">
                                        {album.name}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {album.artists_joined}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {album.release_date} • {album.album_type}
                                    </Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            ) : (
                <ListView
                    items={albums}
                    type="albums"
                    getLargestImage={getLargestImage}
                />
            )}
            <PaginationComponent
                total={total}
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
            />
        </Container>
    );
};

const TracksPage = () => {
    const [tracks, setTracks] = useState<Track[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [total, setTotal] = useState(0);
    const [totalFiltered, setTotalFiltered] = useState<number | null>(null);
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(12);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc' | null>(null);
    const [sortField, setSortField] = useState<'name' | 'duration' | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [view, setView] = useState<'grid' | 'list'>('grid');
    const location = useLocation();
    const navigate = useNavigate();

    const fetchTracks = async () => {
        try {
            setLoading(true);
            const response = await fetch(
                `http://localhost:8001/tracks?page=${page}&limit=${pageSize}${sortOrder ? `&sort=${sortOrder}` : ''}${sortField ? `&field=${sortField}` : ''}${searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''}`
            );
            if (!response.ok) {
                throw new Error('Failed to fetch tracks');
            }
            const data = await response.json();
            setTracks(data.tracks);
            setTotal(data.total);
            setTotalFiltered(data.total_filtered || null);

        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch tracks');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const pageParam = parseInt(params.get('page') || '1');
        const limitParam = parseInt(params.get('limit') || '12');
        const sortParam = params.get('sort') as 'asc' | 'desc' | null;
        const sortFieldParam = params.get('sort_field') as 'name' | 'duration' | null;
        const searchParam = params.get('search') || '';
        setPage(pageParam);
        setPageSize(limitParam);
        setSortOrder(sortParam);
        setSortField(sortFieldParam);
        setSearchQuery(searchParam);
    }, [location]);

    useEffect(() => {
        fetchTracks();
    }, [page, pageSize, sortOrder, sortField, searchQuery]);

    const handleSort = () => {
        const newSortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
        setSortOrder(newSortOrder);
        // Update URL parameters
        const params = new URLSearchParams(location.search);
        params.set('sort', newSortOrder);
        navigate(`${location.pathname}?${params.toString()}`);
    };

    const handleSortFieldChange = (field: 'name' | 'duration') => {
        setSortField(field);
        // Reset to first page when changing sort field
        setPage(1);
        const params = new URLSearchParams(location.search);
        params.set('sort_field', field);
        params.set('page', '1');
        navigate(`${location.pathname}?${params.toString()}`);
    };

    const handleSearch = (query: string) => {
        setSearchQuery(query);
        const params = new URLSearchParams(location.search);
        params.set('search', query);
        params.set('page', '1'); // Reset to first page on search
        navigate(`${location.pathname}?${params.toString()}`);
    };

    if (loading) return <CircularProgress/>;
    if (error) return <Alert severity="error">{error}</Alert>;

    return (
        <Container>
            <Box sx={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3}}>
                <SortablePageTitle
                    title="Tracks"
                    sortOrder={sortOrder}
                    onSort={handleSort}
                    view={view}
                    onViewChange={setView}
                />
                <Box sx={{display: 'flex', gap: 1}}>
                    <Button
                        variant={sortField === 'name' ? 'contained' : 'outlined'}
                        size="small"
                        onClick={() => handleSortFieldChange('name')}
                    >
                        Name
                    </Button>
                    <Button
                        variant={sortField === 'duration' ? 'contained' : 'outlined'}
                        size="small"
                        onClick={() => handleSortFieldChange('duration')}
                    >
                        Duration
                    </Button>
                </Box>
            </Box>
            <SearchFilter
                onSearch={handleSearch}
                placeholder="Search tracks..."
            />
            <Typography variant="subtitle2" sx={{mb: 2}}>
                {searchQuery ? `Search: ${searchQuery}` : ''}
            </Typography>
            <PaginationComponent
                total={total}
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
            />
            <Typography variant="subtitle1" sx={{mb: 2}}>
                {totalFiltered} item{total !== 1 ? 's' : ''} found
                {typeof totalFiltered === 'number' && total !== totalFiltered
                    ? ` (filtered from ${total})`
                    : ''}
            </Typography>
            {view === 'grid' ? (
                <Grid container spacing={3}>
                    {tracks.map((track) => (
                        <Grid item xs={12} sm={6} md={4} key={track.id}>
                            <Card sx={{height: '100%', display: 'flex', flexDirection: 'column'}}>
                                <CardMedia
                                    component="img"
                                    height="200"
                                    image={getLargestImage(track._album.images)}
                                    alt={track.name}
                                />
                                <CardContent sx={{flexGrow: 1}}>
                                    <Typography gutterBottom variant="h5" component="h2">
                                        {track.name}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {track.artists_joined}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {track._album.name} • {formatDuration(track.duration_ms)}
                                    </Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            ) : (
                <ListView
                    items={tracks}
                    type="tracks"
                    getLargestImage={getLargestImage}
                    formatDuration={formatDuration}
                />
            )}
            <PaginationComponent
                total={total}
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
            />
        </Container>
    );
};

const PlaylistsPage = () => {
    const [playlists, setPlaylists] = useState<Playlist[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [total, setTotal] = useState(0);
    const [totalFiltered, setTotalFiltered] = useState<number | null>(null);
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(12);
    const [sortOrder, setSortOrder] = useState<'asc' | 'desc' | null>(null);
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [view, setView] = useState<'grid' | 'list'>('grid');
    const location = useLocation();
    const navigate = useNavigate();

    const fetchPlaylists = async () => {
        try {
            setLoading(true);
            const response = await fetch(`http://localhost:8001/playlists?page=${page}&limit=${pageSize}${sortOrder ? `&sort=${sortOrder}` : ''}${searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''}`);
            if (!response.ok) {
                throw new Error('Failed to fetch playlists');
            }
            const data = await response.json();
            setPlaylists(data.playlists);
            setTotal(data.total);
            setTotalFiltered(data.total_filtered || null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to fetch playlists');
        } finally {
            setLoading(false);
        }
    };

    const handleSearch = (query: string) => {
        setSearchQuery(query);
        const params = new URLSearchParams(location.search);
        params.set('search', query);
        params.set('page', '1'); // Reset to first page on search
        navigate(`${location.pathname}?${params.toString()}`);
    };

    useEffect(() => {
        const params = new URLSearchParams(location.search);
        const pageParam = parseInt(params.get('page') || '1');
        const limitParam = parseInt(params.get('limit') || '12');
        const sortParam = params.get('sort') as 'asc' | 'desc' | null;
        const searchParam = params.get('search') || '';
        setPage(pageParam);
        setPageSize(limitParam);
        setSortOrder(sortParam);
        setSearchQuery(searchParam);
    }, [location]);

    useEffect(() => {
        fetchPlaylists();
    }, [page, pageSize, sortOrder, searchQuery]);

    const handleSort = () => {
        const newSortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
        setSortOrder(newSortOrder);
        // Update URL parameters
        const params = new URLSearchParams(location.search);
        params.set('sort', newSortOrder);
        navigate(`${location.pathname}?${params.toString()}`);
    };

    if (loading) return <CircularProgress/>;
    if (error) return <Alert severity="error">{error}</Alert>;

    return (
        <Container>
            <Box sx={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3}}>
                <SortablePageTitle
                    title="Playlists"
                    sortOrder={sortOrder}
                    onSort={handleSort}
                    view={view}
                    onViewChange={setView}
                />
                <Button
                    variant="contained"
                    color="primary"
                    onClick={() => setCreateDialogOpen(true)}
                >
                    Create Playlist
                </Button>
            </Box>
            <SearchFilter
                onSearch={handleSearch}
                placeholder="Search playlists..."
            />
            <Typography variant="subtitle2" sx={{mb: 2}}>
                {searchQuery ? `Search: ${searchQuery}` : ''}
            </Typography>
            <PaginationComponent
                total={total}
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
            />
            <Typography variant="subtitle1" sx={{mb: 2}}>
                {totalFiltered} item{total !== 1 ? 's' : ''} found
                {typeof totalFiltered === 'number' && total !== totalFiltered
                    ? ` (filtered from ${total})`
                    : ''}
            </Typography>
            {view === 'grid' ? (
                <Grid container spacing={3}>
                    {playlists.map((playlist) => (
                        <Grid item xs={12} sm={6} md={4} key={playlist.id}>
                            <Card sx={{height: '100%', display: 'flex', flexDirection: 'column'}}>
                                <CardMedia
                                    component="img"
                                    height="200"
                                    image={getLargestImage(playlist.images)}
                                    alt={playlist.name}
                                />
                                <CardContent sx={{flexGrow: 1}}>
                                    <Typography gutterBottom variant="h5" component="h2">
                                        {playlist.name}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {playlist.description}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                        {playlist.tracks.total} tracks • {playlist.owner.display_name}
                                    </Typography>
                                </CardContent>
                            </Card>
                        </Grid>
                    ))}
                </Grid>
            ) : (
                <ListView
                    items={playlists}
                    type="playlists"
                    getLargestImage={getLargestImage}
                />
            )}
            <PaginationComponent
                total={total}
                page={page}
                pageSize={pageSize}
                onPageChange={setPage}
                onPageSizeChange={setPageSize}
            />
            <CreatePlaylist
                open={createDialogOpen}
                onClose={() => setCreateDialogOpen(false)}
                onSuccess={() => {
                    // Refresh the playlists list
                    fetchPlaylists();
                }}
            />
        </Container>
    );
};

const App = () => {
    return (
        <Box sx={{display: 'flex', flexDirection: 'column', minHeight: '100vh'}}>
            <Navbar/>
            <Box sx={{display: 'flex', justifyContent: 'flex-end', gap: 2, m: 2}}>

                {/*<Button*/}
                {/*    variant="contained"*/}
                {/*    color="secondary"*/}
                {/*    sx={{m: 2, alignSelf: 'flex-end'}}*/}
                {/*    onClick={async () => {*/}
                {/*        await fetch('http://localhost:8001/save_data_to_mongodb', {method: 'POST'});*/}
                {/*    }}*/}
                {/*>*/}
                {/*    Save Data to Mongo*/}
                {/*</Button>*/}
                <Button
                    variant="contained"
                    color="secondary"
                    sx={{m: 2, alignSelf: 'flex-end'}}
                    onClick={async () => {
                        await fetch('http://localhost:8001/make_playlist_2025', {method: 'POST'});
                    }}
                >
                    Create 2025 Playlist
                </Button>
                <Button
                    variant="contained"
                    color="secondary"
                    sx={{m: 2, alignSelf: 'flex-end'}}
                    onClick={async () => {
                        await fetch('http://localhost:8001/make_playlist_2020s', {method: 'POST'});
                    }}
                >
                    Create 2020s Playlists
                </Button>
                <Button
                    variant="contained"
                    color="secondary"
                    sx={{m: 2, alignSelf: 'flex-end'}}
                    onClick={async () => {
                        await fetch('http://localhost:8001/make_playlist_2010s', {method: 'POST'});
                    }}
                >
                    Create 2010s Playlists
                </Button>
            </Box>
            <Box component="main" sx={{flexGrow: 1, py: 4}}>
                <Routes>
                    <Route path="/" element={<ArtistsPage/>}/>
                    <Route path="/artists" element={<ArtistsPage/>}/>
                    <Route path="/albums" element={<AlbumsPage/>}/>
                    <Route path="/tracks" element={<TracksPage/>}/>
                    <Route path="/playlists" element={<PlaylistsPage/>}/>
                </Routes>
            </Box>
        </Box>
    );
};

export default App; 