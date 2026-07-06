# QuiConvert Backend API

## Base URL

```
/api/pdf
```

---

## Merge PDF

POST

```
/merge
```

Parameters:

- files

---

## Split PDF

POST

```
/split
```

Parameters:

- files
- pages

---

## Compress PDF

POST

```
/compress
```

Parameters:

- files

---

## Rotate PDF

POST

```
/rotate
```

Parameters:

- files
- angle

---

## Rearrange Pages

POST

```
/rearrange
```

Parameters:

- files
- order

---

## Delete Pages

POST

```
/delete-pages
```

Parameters:

- files
- pages

---

## Duplicate Pages

POST

```
/duplicate-pages
```

Parameters:

- files
- pages

---

## Reverse Pages

POST

```
/reverse-pages
```

Parameters:

- files

---

## Watermark

POST

```
/watermark
```

Parameters:

- files
- text
- color
- opacity
- size

---

## Protect PDF

POST

```
/protect
```

Parameters:

- files
- password

---

## Unlock PDF

POST

```
/unlock
```

Parameters:

- files
- password

---

## Page Numbers

POST

```
/page-numbers
```

Parameters:

- files

---

## Image to PDF

POST

```
/image-to-pdf
```

Parameters:

- files
