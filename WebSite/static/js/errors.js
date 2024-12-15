// use "node file_name.js" to run a js file in terminal. Ensure correct path

function noSpaces(event)
        {
            if(event.key.match(/\s/))
            {
                event.preventDefault();
                showRedBox()
            }
        }

        function preventSpacePaste(event)
        {
            const pasted_data = event.clipboardData.getData('text');
            if (pasted_data.match(/\s/))
            {
                event.preventDefault()
                showRedBox()
            }
        }
        
        function showRedBox()
        {
            const errorBox = document.getElementById('errorBox');
            errorBox.style.display = 'block';
            setTimeout(() => 
            {
                errorBox.style.display = 'none';
            }
            , 2000)
        }
        
